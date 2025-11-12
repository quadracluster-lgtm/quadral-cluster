from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from quadral_cluster.database import get_session
from quadral_cluster.domain.socionics import Quadra, SocType
from quadral_cluster.models.availability import Availability
from quadral_cluster.models.preference import Preference
from quadral_cluster.services.matching import (
    ClusterWithScore,
    find_or_create_cluster_for_user,
    list_open_clusters_for_tim,
    try_join_cluster,
)
from quadral_cluster.utils.time_overlap import decode_weekly_mask, ensure_mask_length


router = APIRouter(prefix="", tags=["matching"])


def _parse_quadra(value: str) -> Quadra:
    try:
        return Quadra(value)
    except ValueError as exc:  # pragma: no cover - FastAPI validation fallback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _parse_tim(value: str) -> SocType:
    try:
        return SocType(value)
    except ValueError as exc:  # pragma: no cover - FastAPI validation fallback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _cluster_payload(cluster: ClusterWithScore) -> dict[str, Any]:
    return {
        "cluster_id": cluster.cluster.id,
        "quadra": cluster.cluster.quadra,
        "status": cluster.cluster.status,
        "score": cluster.score,
        "members": [
            {"user_id": member.user_id, "socionics_type": member.socionics_type}
            for member in cluster.members
        ],
    }


@router.get("/clusters/open")
def get_open_clusters(
    quadra: str = Query(...),
    tim: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_session),
) -> list[dict[str, Any]]:
    quadra_enum = _parse_quadra(quadra)
    tim_enum = _parse_tim(tim)
    clusters = list_open_clusters_for_tim(
        quadra_enum, tim_enum, limit=limit, session=session
    )
    return [_cluster_payload(cluster) for cluster in clusters]


@router.post("/clusters/join")
def post_join_cluster(
    payload: dict[str, int], session: Session = Depends(get_session)
) -> dict[str, Any]:
    cluster_id = payload.get("cluster_id")
    user_id = payload.get("user_id")
    if cluster_id is None or user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cluster_id and user_id are required")

    result = try_join_cluster(user_id=user_id, cluster_id=cluster_id, session=session)
    if result.get("ok"):
        return result
    if result.get("reason") == "slot_taken":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slot_taken")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("reason", "unknown_error"))


@router.post("/clusters/find_or_create")
def post_find_or_create(
    payload: dict[str, Any], session: Session = Depends(get_session)
) -> dict[str, Any]:
    user_id = payload.get("user_id")
    quadra_value = payload.get("quadra")
    if user_id is None or quadra_value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id and quadra are required")

    quadra_enum = _parse_quadra(quadra_value)
    result = find_or_create_cluster_for_user(user_id=user_id, quadra=quadra_enum, session=session)
    return result


@router.post("/preferences/like")
def post_preference(
    payload: dict[str, Any], session: Session = Depends(get_session)
) -> dict[str, Any]:
    from_user_id = payload.get("from_user_id")
    to_user_id = payload.get("to_user_id")
    weight = payload.get("weight")
    if from_user_id is None or to_user_id is None or weight is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="from_user_id, to_user_id and weight are required")

    weight_int = int(weight)
    if weight_int < -2 or weight_int > 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weight must be between -2 and 2")

    preference = session.get(Preference, (from_user_id, to_user_id))
    if preference is None:
        preference = Preference(
            from_user_id=from_user_id, to_user_id=to_user_id, weight=weight_int
        )
        session.add(preference)
    else:
        preference.weight = weight_int

    session.flush()
    return {"ok": True}


@router.put("/availability")
def put_availability(
    payload: dict[str, Any], session: Session = Depends(get_session)
) -> dict[str, Any]:
    user_id = payload.get("user_id")
    weekly_mask = payload.get("weekly_mask")
    if user_id is None or weekly_mask is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id and weekly_mask are required")

    bits = (
        [1 if bool(value) else 0 for value in weekly_mask]
        if isinstance(weekly_mask, (list, tuple))
        else decode_weekly_mask(str(weekly_mask))
    )
    mask = ensure_mask_length(bits)
    availability = session.get(Availability, user_id)
    if availability is None:
        availability = Availability(user_id=user_id, weekly_mask=mask)
        session.add(availability)
    else:
        availability.weekly_mask = mask

    session.flush()
    return {"ok": True}
