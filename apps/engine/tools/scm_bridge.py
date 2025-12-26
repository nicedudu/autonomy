from typing import Dict, Any, List
import time
import random
from tools import BaseTool

class SCMBridge(BaseTool):
    """供应链桥梁工具 - 与SCM Agent通信的专用协议"""
    
    def __init__(self):
        super().__init__(
            tool_name="SCM_Bridge",
            description="与SCM Agent通信的专用协议，用于请求成本报价、查询供应商信息、确认库存状态等"
        )
        self.scm_agent_endpoint = "http://localhost:8001/scm_agent"  # 模拟SCM Agent端点
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行SCM通信"""
        start_time = time.time()
        
        try:
            # 解析参数
            action = parameters.get("action", "request_cost_quote")
            products = parameters.get("products", ["product_1"])
            requirements = parameters.get("requirements", {"lead_time": 15, "minimum_order": 100})
            
            # 执行相应的SCM通信动作
            if action == "request_cost_quote":
                result = self._request_cost_quote(products, requirements)
            elif action == "query_supplier_info":
                result = self._query_supplier_info(parameters.get("supplier_id", ""))
            elif action == "confirm_inventory":
                result = self._confirm_inventory(products)
            elif action == "get_logistics_cost":
                result = self._get_logistics_cost(parameters.get("shipping_details", {}))
            else:
                result = {"error": f"不支持的动作: {action}"}
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "result": {
                    "action": action,
                    "scm_response": result,
                    "products": products,
                    "requirements": requirements,
                    "timestamp": time.time()
                },
                "execution_time": execution_time,
                "message": f"成功与SCM Agent通信，执行动作: {action}"
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "error": str(e),
                "message": "与SCM Agent通信失败"
            }
    
    def _request_cost_quote(self, products: List[str], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """请求成本报价"""
        print(f"[SCM_Bridge] 请求成本报价，产品: {products}，要求: {requirements}")
        
        # 模拟SCM Agent响应
        # 实际实现中应调用SCM Agent的API
        time.sleep(0.5)  # 模拟网络延迟
        
        # 生成模拟报价
        quotes = []
        for product in products:
            # 随机生成成本报价
            unit_cost = round(random.uniform(15.0, 50.0), 2)
            shipping_cost = round(random.uniform(5.0, 15.0), 2)
            lead_time = random.randint(7, 30)
            minimum_order = random.randint(50, 500)
            
            quotes.append({
                "product_id": product,
                "supplier_id": f"supplier_{random.randint(1000, 9999)}",
                "unit_cost": unit_cost,
                "shipping_cost": shipping_cost,
                "total_cost": round(unit_cost + shipping_cost, 2),
                "lead_time": lead_time,
                "minimum_order": minimum_order,
                "currency": "USD",
                "valid_until": time.time() + 86400 * 7,  # 7天有效
                "status": "available"
            })
        
        # 检查是否满足要求
        for quote in quotes:
            if requirements.get("lead_time") and quote["lead_time"] > requirements["lead_time"]:
                quote["meets_requirements"] = False
            elif requirements.get("minimum_order") and quote["minimum_order"] > requirements["minimum_order"]:
                quote["meets_requirements"] = False
            else:
                quote["meets_requirements"] = True
        
        return {
            "action": "cost_quote",
            "quotes": quotes,
            "total_quotes": len(quotes),
            "timestamp": time.time(),
            "supplier_count": len(set(quote["supplier_id"] for quote in quotes)),
            "avg_unit_cost": round(sum(quote["unit_cost"] for quote in quotes) / len(quotes), 2),
            "avg_shipping_cost": round(sum(quote["shipping_cost"] for quote in quotes) / len(quotes), 2)
        }
    
    def _query_supplier_info(self, supplier_id: str) -> Dict[str, Any]:
        """查询供应商信息"""
        print(f"[SCM_Bridge] 查询供应商信息，供应商ID: {supplier_id}")
        
        # 模拟SCM Agent响应
        time.sleep(0.3)  # 模拟网络延迟
        
        return {
            "action": "supplier_info",
            "supplier_id": supplier_id,
            "supplier_name": f"供应商_{supplier_id}",
            "rating": round(random.uniform(4.0, 5.0), 1),
            "location": random.choice(["China", "Vietnam", "India", "Mexico"]),
            "years_in_business": random.randint(3, 20),
            "product_categories": random.sample(["electronics", "clothing", "home", "toys", "beauty"], 3),
            "payment_terms": random.choice(["NET 30", "NET 60", "L/C"]),
            "lead_time_range": {
                "min": random.randint(7, 15),
                "max": random.randint(20, 45)
            },
            "minimum_order_amount": round(random.uniform(500, 5000), 2),
            "contact_info": {
                "email": f"contact@{supplier_id}.com",
                "phone": f"+86-{random.randint(10000000000, 19999999999)}"
            }
        }
    
    def _confirm_inventory(self, products: List[str]) -> Dict[str, Any]:
        """确认库存状态"""
        print(f"[SCM_Bridge] 确认库存状态，产品: {products}")
        
        # 模拟SCM Agent响应
        time.sleep(0.4)  # 模拟网络延迟
        
        inventory_status = []
        for product in products:
            inventory_status.append({
                "product_id": product,
                "current_stock": random.randint(0, 1000),
                "available_stock": random.randint(0, 800),
                "lead_time_to_restock": random.randint(0, 30),
                "status": random.choice(["in_stock", "low_stock", "out_of_stock"])
            })
        
        return {
            "action": "inventory_status",
            "inventory_status": inventory_status,
            "timestamp": time.time(),
            "total_products": len(products),
            "in_stock_count": sum(1 for item in inventory_status if item["status"] == "in_stock"),
            "low_stock_count": sum(1 for item in inventory_status if item["status"] == "low_stock"),
            "out_of_stock_count": sum(1 for item in inventory_status if item["status"] == "out_of_stock")
        }
    
    def _get_logistics_cost(self, shipping_details: Dict[str, Any]) -> Dict[str, Any]:
        """获取物流成本估算"""
        print(f"[SCM_Bridge] 获取物流成本估算，详情: {shipping_details}")
        
        # 模拟SCM Agent响应
        time.sleep(0.5)  # 模拟网络延迟
        
        # 模拟不同运输方式的成本
        shipping_options = [
            {
                "carrier": "DHL Express",
                "service_level": "express",
                "estimated_cost": round(random.uniform(25.0, 50.0), 2),
                "estimated_delivery_days": random.randint(3, 7),
                "tracking_available": True,
                "insurance_included": False
            },
            {
                "carrier": "FedEx",
                "service_level": "standard",
                "estimated_cost": round(random.uniform(15.0, 30.0), 2),
                "estimated_delivery_days": random.randint(7, 14),
                "tracking_available": True,
                "insurance_included": False
            },
            {
                "carrier": "UPS",
                "service_level": "economy",
                "estimated_cost": round(random.uniform(8.0, 20.0), 2),
                "estimated_delivery_days": random.randint(14, 28),
                "tracking_available": False,
                "insurance_included": False
            }
        ]
        
        # 选择最佳运输方式（成本最低，同时满足要求）
        best_option = min(shipping_options, key=lambda x: x["estimated_cost"])
        
        return {
            "action": "logistics_cost",
            "shipping_options": shipping_options,
            "best_option": best_option,
            "origin": shipping_details.get("origin", "China"),
            "destination": shipping_details.get("destination", "US"),
            "weight": shipping_details.get("weight", 0.5),
            "dimensions": shipping_details.get("dimensions", {"length": 20, "width": 15, "height": 10}),
            "timestamp": time.time()
        }
