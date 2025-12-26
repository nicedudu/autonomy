from typing import Dict, Any, List
import time
import random
from tools import BaseTool

class MarketScraper(BaseTool):
    """市场爬虫工具 - 模拟人类行为的电商数据爬取"""
    
    def __init__(self):
        super().__init__(
            tool_name="Market_Scraper",
            description="模拟人类行为的电商数据爬取，支持Amazon、eBay、Shopee等平台"
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行市场爬虫"""
        start_time = time.time()
        
        try:
            # 解析参数
            query = parameters.get("query", "")
            platforms = parameters.get("platforms", ["Amazon"])
            analysis_type = parameters.get("analysis_type", "competitor")
            max_results = parameters.get("max_results", 10)
            
            # 执行爬虫，添加反爬延迟
            self._anti_scrape_delay()
            
            # 收集数据
            scraped_data = []
            for platform in platforms:
                platform_data = self._scrape_platform(platform, query, analysis_type, max_results)
                scraped_data.extend(platform_data)
                # 平台间添加延迟
                self._anti_scrape_delay()
            
            # 分析数据
            analysis_result = self._analyze_scraped_data(scraped_data, analysis_type)
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "result": {
                    "query": query,
                    "platforms": platforms,
                    "analysis_type": analysis_type,
                    "scraped_data": scraped_data,
                    "analysis_result": analysis_result,
                    "total_results": len(scraped_data),
                    "timestamp": time.time()
                },
                "execution_time": execution_time,
                "message": f"成功从{len(platforms)}个平台爬取数据"
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "error": str(e),
                "message": "市场爬虫失败"
            }
    
    def _anti_scrape_delay(self):
        """反爬机制 - 随机延迟"""
        # 模拟人类浏览行为的随机延迟（1-5秒）
        delay = random.uniform(1.0, 5.0)
        time.sleep(delay)
        print(f"[Market_Scraper] 反爬延迟: {delay:.2f}秒")
    
    def _scrape_platform(self, platform: str, query: str, analysis_type: str, max_results: int) -> List[Dict[str, Any]]:
        """爬取特定平台数据"""
        if platform == "Amazon":
            return self._scrape_amazon(query, analysis_type, max_results)
        elif platform == "eBay":
            return self._scrape_ebay(query, analysis_type, max_results)
        elif platform == "Shopee":
            return self._scrape_shopee(query, analysis_type, max_results)
        else:
            raise ValueError(f"不支持的平台: {platform}")
    
    def _scrape_amazon(self, query: str, analysis_type: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟爬取Amazon数据"""
        print(f"[Market_Scraper] 爬取Amazon数据: {query}")
        
        # 模拟Amazon搜索结果
        return [
            {
                "platform": "Amazon",
                "product_id": f"B0{random.randint(10000000, 99999999)}",
                "title": f"{query} - 高级版",
                "price": round(random.uniform(29.99, 99.99), 2),
                "sales": random.randint(100, 10000),
                "reviews": random.randint(50, 5000),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "seller": f"Amazon卖家{random.randint(1000, 9999)}",
                "shipping": "Free Shipping",
                "category": "Electronics",
                "timestamp": time.time()
            }
            for _ in range(max_results)
        ]
    
    def _scrape_ebay(self, query: str, analysis_type: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟爬取eBay数据"""
        print(f"[Market_Scraper] 爬取eBay数据: {query}")
        
        # 模拟eBay搜索结果
        return [
            {
                "platform": "eBay",
                "product_id": f"{random.randint(100000000000, 999999999999)}",
                "title": f"{query} - eBay独家",
                "price": round(random.uniform(19.99, 89.99), 2),
                "sales": random.randint(50, 5000),
                "reviews": random.randint(20, 2000),
                "rating": round(random.uniform(3.5, 4.8), 1),
                "seller": f"eBay商家{random.randint(1000, 9999)}",
                "shipping": f"${random.randint(0, 19)}.99 Shipping",
                "category": "Home & Garden",
                "timestamp": time.time()
            }
            for _ in range(max_results)
        ]
    
    def _scrape_shopee(self, query: str, analysis_type: str, max_results: int) -> List[Dict[str, Any]]:
        """模拟爬取Shopee数据"""
        print(f"[Market_Scraper] 爬取Shopee数据: {query}")
        
        # 模拟Shopee搜索结果
        return [
            {
                "platform": "Shopee",
                "product_id": f"{random.randint(100000000, 999999999)}",
                "title": f"{query} - 东南亚爆款",
                "price": round(random.uniform(14.99, 69.99), 2),
                "sales": random.randint(200, 20000),
                "reviews": random.randint(100, 8000),
                "rating": round(random.uniform(4.2, 4.9), 1),
                "seller": f"Shopee卖家{random.randint(1000, 9999)}",
                "shipping": "Free Shipping",
                "category": "Fashion",
                "timestamp": time.time()
            }
            for _ in range(max_results)
        ]
    
    def _analyze_scraped_data(self, scraped_data: List[Dict[str, Any]], analysis_type: str) -> Dict[str, Any]:
        """分析爬取的数据"""
        if analysis_type == "competitor":
            return self._analyze_competitors(scraped_data)
        elif analysis_type == "pricing":
            return self._analyze_pricing(scraped_data)
        elif analysis_type == "market_share":
            return self._analyze_market_share(scraped_data)
        else:
            return self._analyze_general(scraped_data)
    
    def _analyze_competitors(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """竞争对手分析"""
        # 计算基本统计数据
        total_products = len(scraped_data)
        avg_price = sum(product["price"] for product in scraped_data) / total_products if total_products > 0 else 0
        avg_rating = sum(product["rating"] for product in scraped_data) / total_products if total_products > 0 else 0
        total_sales = sum(product["sales"] for product in scraped_data) if total_products > 0 else 0
        
        # 按平台统计
        platform_stats = {}
        for product in scraped_data:
            platform = product["platform"]
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "product_count": 0,
                    "avg_price": 0,
                    "avg_rating": 0,
                    "total_sales": 0,
                    "products": []
                }
            
            platform_stats[platform]["product_count"] += 1
            platform_stats[platform]["avg_price"] += product["price"]
            platform_stats[platform]["avg_rating"] += product["rating"]
            platform_stats[platform]["total_sales"] += product["sales"]
            platform_stats[platform]["products"].append(product)
        
        # 计算平台平均值
        for platform, stats in platform_stats.items():
            count = stats["product_count"]
            stats["avg_price"] = round(stats["avg_price"] / count, 2)
            stats["avg_rating"] = round(stats["avg_rating"] / count, 1)
        
        return {
            "analysis_type": "competitor",
            "total_products": total_products,
            "avg_price": round(avg_price, 2),
            "avg_rating": round(avg_rating, 1),
            "total_sales": total_sales,
            "platform_stats": platform_stats,
            "top_products_by_sales": sorted(scraped_data, key=lambda x: x["sales"], reverse=True)[:5],
            "top_products_by_rating": sorted(scraped_data, key=lambda x: x["rating"], reverse=True)[:5]
        }
    
    def _analyze_pricing(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """定价分析"""
        # 计算价格分布
        prices = [product["price"] for product in scraped_data]
        prices.sort()
        
        # 计算四分位数
        n = len(prices)
        if n > 0:
            q1 = prices[n // 4]
            median = prices[n // 2]
            q3 = prices[3 * n // 4]
            min_price = prices[0]
            max_price = prices[-1]
        else:
            q1 = median = q3 = min_price = max_price = 0
        
        return {
            "analysis_type": "pricing",
            "price_range": {
                "min": min_price,
                "max": max_price,
                "median": median,
                "q1": q1,
                "q3": q3
            },
            "avg_price": round(sum(prices) / len(prices), 2) if prices else 0,
            "price_distribution": self._calculate_price_distribution(prices)
        }
    
    def _analyze_market_share(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """市场份额分析"""
        total_sales = sum(product["sales"] for product in scraped_data) if scraped_data else 1
        
        # 按卖家统计市场份额
        seller_share = {}
        for product in scraped_data:
            seller = product["seller"]
            seller_share[seller] = seller_share.get(seller, 0) + product["sales"]
        
        # 计算百分比
        for seller in seller_share:
            seller_share[seller] = round((seller_share[seller] / total_sales) * 100, 2)
        
        # 按平台统计市场份额
        platform_share = {}
        for product in scraped_data:
            platform = product["platform"]
            platform_share[platform] = platform_share.get(platform, 0) + product["sales"]
        
        for platform in platform_share:
            platform_share[platform] = round((platform_share[platform] / total_sales) * 100, 2)
        
        return {
            "analysis_type": "market_share",
            "total_sales": total_sales,
            "seller_market_share": dict(sorted(seller_share.items(), key=lambda x: x[1], reverse=True)),
            "platform_market_share": dict(sorted(platform_share.items(), key=lambda x: x[1], reverse=True))
        }
    
    def _analyze_general(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """通用分析"""
        return {
            "analysis_type": "general",
            "total_products": len(scraped_data),
            "platform_distribution": self._calculate_platform_distribution(scraped_data),
            "avg_product_data": {
                "avg_price": round(sum(p["price"] for p in scraped_data) / len(scraped_data), 2) if scraped_data else 0,
                "avg_rating": round(sum(p["rating"] for p in scraped_data) / len(scraped_data), 1) if scraped_data else 0,
                "avg_reviews": round(sum(p["reviews"] for p in scraped_data) / len(scraped_data), 0) if scraped_data else 0
            }
        }
    
    def _calculate_price_distribution(self, prices: List[float]) -> Dict[str, int]:
        """计算价格分布"""
        distribution = {
            "0-20": 0,
            "20-50": 0,
            "50-100": 0,
            "100+": 0
        }
        
        for price in prices:
            if price < 20:
                distribution["0-20"] += 1
            elif price < 50:
                distribution["20-50"] += 1
            elif price < 100:
                distribution["50-100"] += 1
            else:
                distribution["100+"] += 1
        
        return distribution
    
    def _calculate_platform_distribution(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """计算平台分布"""
        distribution = {}
        for product in scraped_data:
            platform = product["platform"]
            distribution[platform] = distribution.get(platform, 0) + 1
        return distribution
