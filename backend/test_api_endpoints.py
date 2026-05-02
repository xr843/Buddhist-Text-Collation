#!/usr/bin/env python3
"""
API端点快速测试
验证所有新增的API路由是否正常注册
"""
from app.main import app
from fastapi.routing import APIRoute

def test_api_routes():
    """测试所有API路由"""
    print("=" * 60)
    print("API端点测试")
    print("=" * 60)

    # 收集所有路由
    routes = {}
    for route in app.routes:
        if isinstance(route, APIRoute):
            path = route.path
            methods = route.methods
            name = route.name

            if path not in routes:
                routes[path] = []
            routes[path].append({
                'methods': methods,
                'name': name
            })

    # 检查关键端点
    critical_endpoints = {
        'CBETA API': [
            '/api/v1/cbeta/search',
            '/api/v1/cbeta/fetch/{sutra_id}',
            '/api/v1/cbeta/contribution-report',
        ],
        '导出API': [
            '/api/v1/export/collation',
            '/api/v1/export/phylogeny',
        ],
        '对勘API': [
            '/api/v1/comparison/compare',
            '/api/v1/multi-collation/compare',
        ],
    }

    print("\n✅ 已注册的API端点：\n")

    # 按分类显示
    for category, endpoints in critical_endpoints.items():
        print(f"📁 {category}")
        found_count = 0
        for endpoint in endpoints:
            if endpoint in routes:
                methods = routes[endpoint][0]['methods']
                methods_str = ', '.join(sorted(methods - {'HEAD', 'OPTIONS'}))
                print(f"   ✅ {endpoint:<50} [{methods_str}]")
                found_count += 1
            else:
                print(f"   ❌ {endpoint:<50} [未找到]")
        print(f"   小计: {found_count}/{len(endpoints)} 个端点\n")

    # 显示所有路由（按路径排序）
    print("\n" + "=" * 60)
    print("完整路由列表（按路径排序）")
    print("=" * 60 + "\n")

    sorted_routes = sorted(routes.keys())
    for path in sorted_routes:
        if path.startswith('/api/v1'):
            route_info = routes[path][0]
            methods = route_info['methods'] - {'HEAD', 'OPTIONS'}
            methods_str = ', '.join(sorted(methods))
            print(f"{path:<60} [{methods_str}]")

    print("\n" + "=" * 60)
    print(f"✅ 总计: {len([p for p in routes.keys() if p.startswith('/api/v1')])} 个API端点")
    print("=" * 60)

if __name__ == "__main__":
    test_api_routes()
