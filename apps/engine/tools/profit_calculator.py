from typing import Dict, Any, List
import time
import random
from tools import BaseTool

class ProfitCalculator(BaseTool):
    """利润计算器工具 - 内嵌全球税费、汇率和运费计算模块"""
    
    def __init__(self):
        super().__init__(
            tool_name="Profit_Calculator",
            description="全球税费、汇率和运费计算工具，用于盈亏平衡点分析和多场景利润预测"
        )
        # 初始化税率表、汇率表等数据
        self._initialize_data_tables()
    
    def _initialize_data_tables(self):
        """初始化数据表格（模拟实现）"""
        # 模拟税率表
        self.tax_rates = {
            "US": {
                "import_tax": 0.02,  # 进口税
                "sales_tax": 0.08,    # 销售税
                "vat": 0.0,           # 增值税
                "duty_free_threshold": 800  # 免税额度（美元）
            },
            "EU": {
                "import_tax": 0.05,
                "sales_tax": 0.0,
                "vat": 0.2,          # 20%增值税
                "duty_free_threshold": 150  # 免税额度（欧元）
            },
            "JP": {
                "import_tax": 0.03,
                "sales_tax": 0.0,
                "vat": 0.1,          # 10%消费税
                "duty_free_threshold": 10000  # 免税额度（日元）
            },
            "AU": {
                "import_tax": 0.04,
                "sales_tax": 0.0,
                "vat": 0.1,          # 10%商品及服务税
                "duty_free_threshold": 1000  # 免税额度（澳元）
            }
        }
        
        # 模拟实时汇率（实际实现中应调用汇率API）
        self.exchange_rates = {
            "USD": 1.0,       # 基准货币
            "EUR": 0.92,      # 欧元
            "JPY": 148.50,    # 日元
            "AUD": 1.52,      # 澳元
            "CNY": 7.25       # 人民币
        }
        
        # 模拟运费计算规则
        self.shipping_rates = {
            "express": {
                "base_rate": 25.0,  # 基础运费（美元）
                "per_kg": 5.0,      # 每公斤附加费
                "max_delivery_days": 5
            },
            "standard": {
                "base_rate": 15.0,
                "per_kg": 3.0,
                "max_delivery_days": 15
            },
            "economy": {
                "base_rate": 8.0,
                "per_kg": 1.5,
                "max_delivery_days": 30
            }
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行利润计算"""
        start_time = time.time()
        
        try:
            # 解析参数
            product_costs = parameters.get("product_costs", {"unit_cost": 20.0})
            market_data = parameters.get("market_data", {"target_price": 50.0})
            target_regions = parameters.get("target_regions", ["US"])
            scenarios = parameters.get("scenarios", ["base"])
            
            # 执行利润计算
            results = self._calculate_profitability(product_costs, market_data, target_regions, scenarios)
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "result": {
                    "product_costs": product_costs,
                    "market_data": market_data,
                    "target_regions": target_regions,
                    "scenarios": scenarios,
                    "profitability_results": results,
                    "exchange_rates": self.exchange_rates,
                    "timestamp": time.time()
                },
                "execution_time": execution_time,
                "message": f"成功计算{len(target_regions)}个地区，{len(scenarios)}个场景的利润"
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "result": None,
                "execution_time": execution_time,
                "error": str(e),
                "message": "利润计算失败"
            }
    
    def _calculate_profitability(self, product_costs: Dict[str, Any], market_data: Dict[str, Any], 
                               target_regions: List[str], scenarios: List[str]) -> Dict[str, Any]:
        """计算不同地区和场景的盈利能力"""
        results = {}
        
        for region in target_regions:
            region_results = {}
            
            for scenario in scenarios:
                # 获取场景参数
                scenario_params = self._get_scenario_parameters(scenario, product_costs, market_data)
                
                # 计算各项成本
                unit_cost = scenario_params["unit_cost"]
                target_price = scenario_params["target_price"]
                sales_volume = scenario_params["sales_volume"]
                
                # 计算运费
                shipping_cost = self._calculate_shipping_cost(region, product_costs.get("weight", 0.5), product_costs.get("dimensions", {"length": 20, "width": 15, "height": 10}))
                
                # 计算税费
                taxes = self._calculate_taxes(region, unit_cost, target_price)
                
                # 计算平台佣金（假设为15%）
                platform_fee = target_price * 0.15
                
                # 计算广告费用（根据场景调整）
                ad_cost = self._calculate_ad_cost(scenario, target_price)
                
                # 计算单位利润
                unit_profit = target_price - unit_cost - shipping_cost - sum(taxes.values()) - platform_fee - ad_cost
                
                # 计算总利润
                total_profit = unit_profit * sales_volume
                
                # 计算利润率
                profit_margin = (unit_profit / target_price) * 100 if target_price > 0 else 0
                
                # 计算盈亏平衡点
                break_even_point = self._calculate_break_even_point(unit_cost, shipping_cost, sum(taxes.values()), platform_fee, ad_cost, target_price)
                
                region_results[scenario] = {
                    "scenario": scenario,
                    "unit_cost": round(unit_cost, 2),
                    "target_price": round(target_price, 2),
                    "shipping_cost": round(shipping_cost, 2),
                    "taxes": {k: round(v, 2) for k, v in taxes.items()},
                    "platform_fee": round(platform_fee, 2),
                    "ad_cost": round(ad_cost, 2),
                    "unit_profit": round(unit_profit, 2),
                    "sales_volume": sales_volume,
                    "total_profit": round(total_profit, 2),
                    "profit_margin": round(profit_margin, 2),
                    "break_even_point": round(break_even_point, 0),
                    "currency": self._get_region_currency(region)
                }
            
            results[region] = region_results
        
        return results
    
    def _get_scenario_parameters(self, scenario: str, product_costs: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取场景参数"""
        base_unit_cost = product_costs.get("unit_cost", 20.0)
        base_target_price = market_data.get("target_price", 50.0)
        base_sales_volume = market_data.get("expected_sales", 1000)
        
        scenario_params = {
            "base": {
                "unit_cost": base_unit_cost,
                "target_price": base_target_price,
                "sales_volume": base_sales_volume
            },
            "best": {
                "unit_cost": base_unit_cost * 0.9,  # 成本降低10%
                "target_price": base_target_price * 1.1,  # 售价提高10%
                "sales_volume": base_sales_volume * 1.5  # 销量提高50%
            },
            "worst": {
                "unit_cost": base_unit_cost * 1.1,  # 成本提高10%
                "target_price": base_target_price * 0.9,  # 售价降低10%
                "sales_volume": base_sales_volume * 0.5  # 销量降低50%
            }
        }
        
        return scenario_params.get(scenario, scenario_params["base"])
    
    def _calculate_shipping_cost(self, region: str, weight: float, dimensions: Dict[str, float]) -> float:
        """计算运费"""
        # 选择运输方式（这里简化为统一使用standard）
        shipping_type = "standard"
        rates = self.shipping_rates[shipping_type]
        
        # 计算体积重量（长×宽×高/5000，单位：cm）
        volume_weight = (dimensions["length"] * dimensions["width"] * dimensions["height"]) / 5000
        
        # 取实际重量和体积重量中的较大值
        chargeable_weight = max(weight, volume_weight)
        
        # 计算基础运费
        base_shipping = rates["base_rate"]
        
        # 计算附加运费（每公斤）
        additional_shipping = rates["per_kg"] * chargeable_weight
        
        # 总运费
        total_shipping = base_shipping + additional_shipping
        
        # 根据地区调整运费（模拟不同地区的运费差异）
        region_adjustment = {
            "US": 1.0,
            "EU": 1.2,
            "JP": 1.1,
            "AU": 1.3
        }.get(region, 1.0)
        
        return total_shipping * region_adjustment
    
    def _calculate_taxes(self, region: str, unit_cost: float, target_price: float) -> Dict[str, float]:
        """计算税费"""
        if region not in self.tax_rates:
            return {"taxes": 0.0}
        
        tax_rules = self.tax_rates[region]
        taxes = {}
        
        # 计算进口税
        if unit_cost > tax_rules["duty_free_threshold"]:
            taxes["import_tax"] = unit_cost * tax_rules["import_tax"]
        else:
            taxes["import_tax"] = 0.0
        
        # 计算销售税
        taxes["sales_tax"] = target_price * tax_rules["sales_tax"]
        
        # 计算增值税/VAT
        taxes["vat"] = target_price * tax_rules["vat"]
        
        return taxes
    
    def _calculate_ad_cost(self, scenario: str, target_price: float) -> float:
        """计算广告费用"""
        # 根据场景调整广告费用占比
        ad_cost_ratios = {
            "best": 0.10,   # 10%广告费用
            "base": 0.15,   # 15%广告费用
            "worst": 0.20   # 20%广告费用
        }
        
        ratio = ad_cost_ratios.get(scenario, 0.15)
        return target_price * ratio
    
    def _calculate_break_even_point(self, unit_cost: float, shipping_cost: float, total_taxes: float, 
                                  platform_fee: float, ad_cost: float, target_price: float) -> float:
        """计算盈亏平衡点（销售量）"""
        # 单位固定成本
        unit_fixed_cost = unit_cost + shipping_cost + total_taxes
        
        # 单位可变成本
        unit_variable_cost = platform_fee + ad_cost
        
        # 单位总成本
        unit_total_cost = unit_fixed_cost + unit_variable_cost
        
        # 单位边际贡献
        unit_contribution = target_price - unit_total_cost
        
        # 盈亏平衡点（假设固定成本为0，因为这里主要计算的是单位产品的盈亏平衡销售量）
        # 实际计算中应考虑固定成本，这里简化处理
        if unit_contribution > 0:
            return 1  # 至少销售1件即可盈利
        else:
            # 计算需要达到多少售价才能盈利
            return abs(unit_contribution) / target_price * 100  # 返回需要提高的售价百分比
    
    def _get_region_currency(self, region: str) -> str:
        """获取地区对应的货币"""
        currency_map = {
            "US": "USD",
            "EU": "EUR",
            "JP": "JPY",
            "AU": "AUD"
        }
        return currency_map.get(region, "USD")
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """货币转换"""
        if from_currency == to_currency:
            return amount
        
        # 先转换为USD，再转换为目标货币
        usd_amount = amount / self.exchange_rates[from_currency] if from_currency != "USD" else amount
        target_amount = usd_amount * self.exchange_rates[to_currency]
        
        return target_amount
