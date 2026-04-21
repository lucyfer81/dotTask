from app import db
from app.models import Location


def get_matching_locations(scope_type, scope_detail):
    """根据 scope_type 和 scope_detail 返回匹配的活跃地点列表。"""
    query = Location.query.filter_by(is_active=True)

    if scope_type == "All":
        pass
    elif scope_type == "Country":
        if scope_detail:
            query = query.filter_by(country=scope_detail)
    elif scope_type == "Location_Type":
        if scope_detail:
            query = query.filter_by(location_type=scope_detail)
    elif scope_type == "Region":
        if scope_detail:
            query = query.filter_by(region=scope_detail)
    elif scope_type == "Manual":
        return []

    return query.order_by(Location.location_name).all()


def get_scope_preview(scope_type, scope_detail):
    """返回匹配数量和地点名称列表，用于预览。"""
    locations = get_matching_locations(scope_type, scope_detail)
    return {
        "count": len(locations),
        "names": [loc.location_name for loc in locations],
    }
