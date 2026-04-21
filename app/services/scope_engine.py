from app import db
from app.models import Location


def get_filtered_locations(country=None, location_type=None):
    """根据 country 和 location_type 筛选活跃地点。两者都是可选的。"""
    query = Location.query.filter_by(is_active=True)

    if country:
        query = query.filter_by(country=country)
    if location_type:
        query = query.filter_by(location_type=location_type)

    return query.order_by(Location.location_name).all()


def get_scope_preview(country=None, location_type=None):
    """返回匹配的地点列表，用于预览。"""
    locations = get_filtered_locations(country, location_type)
    return {
        "locations": [
            {"id": loc.id, "name": loc.location_name, "country": loc.country, "type": loc.location_type}
            for loc in locations
        ],
    }


def get_distinct_countries():
    """获取所有活跃地点的不重复 country 列表。"""
    results = db.session.execute(
        db.text("SELECT DISTINCT country FROM location_master WHERE is_active = 1 AND country IS NOT NULL ORDER BY country")
    ).fetchall()
    return [r[0] for r in results]


def get_distinct_location_types():
    """获取所有活跃地点的不重复 location_type 列表。"""
    results = db.session.execute(
        db.text("SELECT DISTINCT location_type FROM location_master WHERE is_active = 1 AND location_type IS NOT NULL ORDER BY location_type")
    ).fetchall()
    return [r[0] for r in results]
