from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import Base, engine, get_session
from ..models.domain import (
    Application,
    Cluster,
    ClusterMembership,
    Profile,
    TestResult,
    User,
)
from ..schemas import (
    ApplicationCreate,
    ApplicationRead,
    ClusterCreate,
    ClusterRead,
    Recommendation,
    TestResultCreate,
    TestResultRead,
    UserCreate,
    UserRead,
)
from ..services.matchmaking import score_candidate_for_cluster


Base.metadata.create_all(bind=engine)

router = APIRouter()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, session: Session = Depends(get_session)) -> UserRead:
    user = User(telegram_id=payload.telegram_id, username=payload.username, email=payload.email)
    profile = Profile(**payload.profile.model_dump())
    user.profile = profile
    session.add(user)
    session.flush()
    session.refresh(user)
    return UserRead.model_validate(user)


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)) -> UserRead:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


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


@router.get("/clusters/{cluster_id}", response_model=ClusterRead)
def get_cluster(cluster_id: int, session: Session = Depends(get_session)) -> ClusterRead:
    cluster = session.get(Cluster, cluster_id)
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    return ClusterRead.model_validate(cluster)


@router.get("/matchmaking/recommendations", response_model=List[Recommendation])
def get_recommendations(user_id: int, limit: int = 10, session: Session = Depends(get_session)) -> List[Recommendation]:
    user = session.get(User, user_id)
    if user is None or user.profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    clusters = (
        session.query(Cluster)
        .filter(~Cluster.memberships.any(ClusterMembership.user_id == user_id))
        .limit(limit * 5)  # fetch a wider set before trimming
        .all()
    )

    recommendations: List[Recommendation] = []
    for cluster in clusters:
        score = score_candidate_for_cluster(user.profile, cluster, cluster.memberships)
        recommendations.append(
            Recommendation(cluster=ClusterRead.model_validate(cluster), compatibility_score=score)
        )

    recommendations.sort(key=lambda rec: rec.compatibility_score, reverse=True)
    return recommendations[:limit]


@router.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, session: Session = Depends(get_session)) -> ApplicationRead:
    user = session.get(User, payload.user_id)
    cluster = session.get(Cluster, payload.cluster_id)
    if user is None or user.profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    if session.query(ClusterMembership).filter_by(user_id=user.id, cluster_id=cluster.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already in cluster")

    compatibility = score_candidate_for_cluster(user.profile, cluster, cluster.memberships)
    application = Application(
        user_id=user.id,
        cluster_id=cluster.id,
        status="pending",
        compatibility_score=compatibility,
    )
    session.add(application)
    session.flush()
    session.refresh(application)
    return ApplicationRead.model_validate(application)


@router.post("/tests", response_model=TestResultRead, status_code=status.HTTP_201_CREATED)
def create_test_result(payload: TestResultCreate, session: Session = Depends(get_session)) -> TestResultRead:
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
