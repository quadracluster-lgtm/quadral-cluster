from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from quadral_cluster.database import get_session
from quadral_cluster.models.domain import (
    Application,
    ApplicationStatusEnum,
    Cluster,
    ClusterMembership,
    Profile,
    TestResult,
    User,
)
from quadral_cluster.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ClusterCreate,
    ClusterRead,
    CompatibilityBreakdownRead,
    ProfileRead,
    ProfileUpdate,
    Recommendation,
    TestResultCreate,
    TestResultRead,
    UserCreate,
    UserRead,
)
from quadral_cluster.services.matchmaking import evaluate_candidate

if TYPE_CHECKING:  # pragma: no cover - type checking helper
    from quadral_cluster.services.matchmaking import CompatibilityBreakdown


router = APIRouter()


def _ensure_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _ensure_profile(user: User) -> Profile:
    profile = user.profile
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return profile


def _to_breakdown_schema(breakdown: "CompatibilityBreakdown") -> CompatibilityBreakdownRead:
    return CompatibilityBreakdownRead(**breakdown.__dict__)


def _matches_candidate_age(memberships: Iterable[ClusterMembership], candidate_age: int) -> bool:
    ages = [
        membership.user.profile.age
        for membership in memberships
        if membership.user.profile and membership.user.profile.age is not None
    ]
    if not ages:
        return True
    avg_age = sum(ages) / len(ages)
    return abs(candidate_age - avg_age) <= 5


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    user = User(telegram_id=payload.telegram_id, username=payload.username, email=payload.email)
    profile = Profile(**payload.profile.model_dump())
    user.profile = profile
    session.add(user)
    session.flush()
    session.refresh(user)
    return UserRead.model_validate(user)


@router.get("/users", response_model=List[UserRead])
def list_users(session: Session = Depends(get_session)) -> List[UserRead]:
    users = session.query(User).options(selectinload(User.profile)).all()
    return [UserRead.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)) -> UserRead:
    user = _ensure_user(session, user_id)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}/profile", response_model=ProfileRead)
def update_profile(
    user_id: int, payload: ProfileUpdate, session: Session = Depends(get_session)
) -> ProfileRead:
    user = _ensure_user(session, user_id)
    profile = _ensure_profile(user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    session.flush()
    session.refresh(profile)
    return ProfileRead.model_validate(profile)


@router.get("/users/{user_id}/applications", response_model=List[ApplicationRead])
def list_user_applications(user_id: int, session: Session = Depends(get_session)) -> List[ApplicationRead]:
    _ensure_user(session, user_id)
    applications = (
        session.query(Application)
        .filter(Application.user_id == user_id)
        .options(selectinload(Application.cluster))
        .order_by(Application.created_at.desc())
        .all()
    )
    return [ApplicationRead.model_validate(application) for application in applications]


@router.get("/users/{user_id}/tests", response_model=List[TestResultRead])
def list_user_tests(user_id: int, session: Session = Depends(get_session)) -> List[TestResultRead]:
    _ensure_user(session, user_id)
    results = (
        session.query(TestResult)
        .filter(TestResult.user_id == user_id)
        .order_by(TestResult.created_at.desc())
        .all()
    )
    return [TestResultRead.model_validate(result) for result in results]


@router.post("/clusters", response_model=ClusterRead, status_code=status.HTTP_201_CREATED)
def create_cluster(payload: ClusterCreate, session: Session = Depends(get_session)) -> ClusterRead:
    cluster = Cluster(
        name=payload.name,
        language=payload.language,
        city=payload.city,
        timezone=payload.timezone,
        target_quadra=payload.target_quadra,
        target_psychotype=payload.target_psychotype,
        activity_score=payload.activity_score,
        reputation_score=payload.reputation_score,
    )
    session.add(cluster)
    session.flush()

    if payload.founder_user_id is not None:
        founder = session.get(User, payload.founder_user_id)
        if founder is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Founder user not found")
        membership = ClusterMembership(cluster_id=cluster.id, user_id=founder.id, role="founder")
        session.add(membership)

    session.refresh(cluster)
    return ClusterRead.model_validate(cluster)


@router.get("/clusters", response_model=List[ClusterRead])
def list_clusters(session: Session = Depends(get_session)) -> List[ClusterRead]:
    clusters = session.query(Cluster).all()
    return [ClusterRead.model_validate(cluster) for cluster in clusters]


@router.get("/clusters/search", response_model=List[ClusterRead])
def search_clusters(
    language: str | None = None,
    city: str | None = None,
    timezone: str | None = None,
    min_activity: float | None = None,
    min_reputation: float | None = None,
    candidate_age: int | None = None,
    limit: int = 20,
    session: Session = Depends(get_session),
) -> List[ClusterRead]:
    query = session.query(Cluster).options(
        selectinload(Cluster.memberships)
        .selectinload(ClusterMembership.user)
        .selectinload(User.profile)
    )

    if language:
        query = query.filter(Cluster.language == language)
    if city:
        query = query.filter(Cluster.city == city)
    if timezone:
        query = query.filter(Cluster.timezone == timezone)
    if min_activity is not None:
        query = query.filter(Cluster.activity_score >= min_activity)
    if min_reputation is not None:
        query = query.filter(Cluster.reputation_score >= min_reputation)

    query = query.order_by(Cluster.created_at.desc()).limit(limit * 3)
    clusters = query.all()

    if candidate_age is not None:
        clusters = [cluster for cluster in clusters if _matches_candidate_age(cluster.memberships, candidate_age)]

    return [ClusterRead.model_validate(cluster) for cluster in clusters[:limit]]


@router.get("/clusters/{cluster_id}", response_model=ClusterRead)
def get_cluster(cluster_id: int, session: Session = Depends(get_session)) -> ClusterRead:
    cluster = session.get(Cluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return ClusterRead.model_validate(cluster)


@router.get("/matchmaking/recommendations", response_model=List[Recommendation])
def get_recommendations(user_id: int, limit: int = 10, session: Session = Depends(get_session)) -> List[Recommendation]:
    user = _ensure_user(session, user_id)
    profile = _ensure_profile(user)

    clusters = (
        session.query(Cluster)
        .filter(~Cluster.memberships.any(ClusterMembership.user_id == user_id))
        .options(
            selectinload(Cluster.memberships)
            .selectinload(ClusterMembership.user)
            .selectinload(User.profile)
        )
        .limit(limit * 5)
        .all()
    )

    recommendations: List[Recommendation] = []
    for cluster in clusters:
        score, breakdown = evaluate_candidate(profile, cluster, cluster.memberships)
        recommendations.append(
            Recommendation(
                cluster=ClusterRead.model_validate(cluster),
                compatibility_score=score,
                breakdown=_to_breakdown_schema(breakdown),
            )
        )

    recommendations.sort(key=lambda rec: rec.compatibility_score, reverse=True)
    return recommendations[:limit]


@router.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, session: Session = Depends(get_session)) -> ApplicationRead:
    user = _ensure_user(session, payload.user_id)
    profile = _ensure_profile(user)
    cluster = session.get(Cluster, payload.cluster_id)
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    if session.query(ClusterMembership).filter_by(user_id=user.id, cluster_id=cluster.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already in cluster")

    compatibility, _ = evaluate_candidate(profile, cluster, cluster.memberships)
    application = Application(
        user_id=user.id,
        cluster_id=cluster.id,
        status=ApplicationStatusEnum.PENDING,
        compatibility_score=compatibility,
    )
    session.add(application)
    session.flush()
    session.refresh(application)
    return ApplicationRead.model_validate(application)


@router.post("/tests", response_model=TestResultRead, status_code=status.HTTP_201_CREATED)
def create_test_result(payload: TestResultCreate, session: Session = Depends(get_session)) -> TestResultRead:
    user = _ensure_user(session, payload.user_id)

    result = TestResult(
        user_id=payload.user_id,
        test_type=payload.test_type,
        socionics_type=payload.socionics_type,
        psychotype=payload.psychotype,
        confidence=payload.confidence,
    )
    session.add(result)

    if payload.socionics_type or payload.psychotype:
        profile = user.profile
        if profile:
            if payload.socionics_type:
                profile.socionics_type = payload.socionics_type
            if payload.psychotype:
                profile.psychotype = payload.psychotype

    session.flush()
    session.refresh(result)
    return TestResultRead.model_validate(result)
