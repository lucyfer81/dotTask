from app import db
from app.models import Location
from app.dropdowns import get_options


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
    """获取所有 country 选项列表（来自配置文件）。"""
    return get_options("countries")


def get_distinct_location_types():
    """获取所有 location_type 选项列表（来自配置文件）。"""
    return get_options("location_types")
