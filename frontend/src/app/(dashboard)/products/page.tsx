"use client";

import { useState } from "react";
import { Package, TrendingUp, TrendingDown, Minus, AlertTriangle, Plus, Settings, ChevronDown, ChevronUp } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const INITIAL_PRODUCTS: Array<{ name: string; platform: string; status: string; stage: string; sales: number; revenue: number; margin: string; daysListed: number }> = [];

const STAGE_COLORS: Record<string, string> = {
  "加量": "text-green-400 border-green-500/30 bg-green-500/10",
  "维持": "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
  "内容就绪": "text-indigo-400 border-indigo-500/30 bg-indigo-500/10",
  "待淘汰": "text-red-400 border-red-500/30 bg-red-500/10",
};

const STRATEGY_OPTIONS = [
  { label: "换供应商", icon: "🔄" },
  { label: "换内容方向", icon: "✏️" },
  { label: "调价", icon: "💰" },
  { label: "换平台", icon: "🌐" },
];

type ProductItem = typeof INITIAL_PRODUCTS[0];

function AddProductForm({ onAdd }: { onAdd: (p: ProductItem) => void }) {
  const [showForm, setShowForm] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: "", category: "", price: "", link: "" });

  const handleAdd = () => {
    if (!newProduct.name.trim()) return;
    onAdd({
      name: newProduct.name.trim(),
      platform: newProduct.category || "未分类",
      status: "content_ready",
      stage: "内容就绪",
      sales: 0,
      revenue: Number(newProduct.price) || 0,
      margin: "0%",
      daysListed: 0,
    });
    setNewProduct({ name: "", category: "", price: "", link: "" });
    setShowForm(false);
  };

  return (
    <div>
      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-1.5 text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          手动添加商品
        </button>
      ) : (
        <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/5 p-4 space-y-3">
          <div className="text-sm font-medium text-cyan-400">添加新商品</div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">商品名 *</label>
              <input type="text" value={newProduct.name} onChange={(e) => setNewProduct((p) => ({ ...p, name: e.target.value }))}
                placeholder="输入商品名称" className="w-full text-xs rounded-lg border border-border/50 bg-background px-3 py-2 outline-none focus:border-cyan-500/50" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">品类</label>
              <input type="text" value={newProduct.category} onChange={(e) => setNewProduct((p) => ({ ...p, category: e.target.value }))}
                placeholder="如：抖音、拼多多" className="w-full text-xs rounded-lg border border-border/50 bg-background px-3 py-2 outline-none focus:border-cyan-500/50" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">价格</label>
              <input type="number" value={newProduct.price} onChange={(e) => setNewProduct((p) => ({ ...p, price: e.target.value }))}
                placeholder="0.00" className="w-full text-xs rounded-lg border border-border/50 bg-background px-3 py-2 outline-none focus:border-cyan-500/50" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">1688链接（可选）</label>
              <input type="text" value={newProduct.link} onChange={(e) => setNewProduct((p) => ({ ...p, link: e.target.value }))}
                placeholder="https://..." className="w-full text-xs rounded-lg border border-border/50 bg-background px-3 py-2 outline-none focus:border-cyan-500/50" />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => { setShowForm(false); setNewProduct({ name: "", category: "", price: "", link: "" }); }}
              className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 transition-colors">取消</button>
            <button onClick={handleAdd} disabled={!newProduct.name.trim()}
              className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">添加</button>
          </div>
        </div>
      )}
    </div>
  );
}

function ProductsReviewView({ products, onAddProduct }: { products: ProductItem[]; onAddProduct: (p: ProductItem) => void }) {
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2000);
  };

  return (
    <div className="space-y-4 relative">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-cyan-500/90 text-white text-xs rounded-lg px-4 py-2 shadow-lg animate-in fade-in slide-in-from-top-2">
          {toastMessage}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">所有在管商品及其生命周期状态：</div>
        <AddProductForm onAdd={onAddProduct} />
      </div>

      {/* Product Cards */}
      {products.map((p) => (
        <div key={p.name} className="rounded-xl border border-border/50 overflow-hidden">
          <div className="p-4 flex items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm">{p.name}</span>
                <Badge variant="outline" className="text-[10px]">{p.platform}</Badge>
                <Badge variant="outline" className={`text-[10px] ${STAGE_COLORS[p.stage] || ""}`}>
                  {p.stage}
                </Badge>
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                <span>销量 {p.sales}</span>
                <span>营收 ¥{p.revenue}</span>
                <span>利润率 {p.margin}</span>
                <span>{p.daysListed > 0 ? `上架 ${p.daysListed} 天` : "未上架"}</span>
              </div>
            </div>
            <div className="flex gap-2 items-center">
              {p.stage === "待淘汰" && (
                <>
                  <button className="text-xs border border-red-500/30 text-red-400 rounded-lg px-3 py-1.5 hover:bg-red-500/10">
                    确认淘汰
                  </button>
                  <button className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50">
                    再观察
                  </button>
                </>
              )}
              {p.stage === "加量" && (
                <button className="text-xs border border-green-500/30 text-green-400 rounded-lg px-3 py-1.5 hover:bg-green-500/10">
                  查看加量计划
                </button>
              )}
              {(p.stage === "待淘汰" || p.stage === "加量") && (
                <button
                  onClick={() => setExpandedStrategy(expandedStrategy === p.name ? null : p.name)}
                  className="flex items-center gap-1 text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 transition-colors"
                >
                  <Settings className="h-3 w-3" />
                  调整策略
                  {expandedStrategy === p.name ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              )}
            </div>
          </div>
          {/* Strategy Panel */}
          {expandedStrategy === p.name && (
            <div className="border-t border-border/50 bg-muted/20 px-4 py-3">
              <div className="text-xs text-muted-foreground mb-2">选择调整策略：</div>
              <div className="flex gap-2 flex-wrap">
                {STRATEGY_OPTIONS.map((opt) => (
                  <button
                    key={opt.label}
                    onClick={() => showToast(`已选择「${opt.label}」，将为「${p.name}」执行策略调整`)}
                    className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 transition-colors"
                  >
                    {opt.icon} {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function ProductsPage() {
  const [products, setProducts] = useState(INITIAL_PRODUCTS);

  const handleAddProduct = (p: ProductItem) => {
    setProducts((prev) => [...prev, p]);
  };

  return (
    <ModulePageLayout
      moduleId="evaluation"
      title="在管商品"
      autoView={
        <AutoModePanel
          moduleId="evaluation"
          icon={<Package className="h-5 w-5" />}
          description="自动监控所有在管商品表现，7天后自动做出加量/维持/淘汰决策"
          quickActions={<AddProductForm onAdd={handleAddProduct} />}
          metrics={[
            { label: "在管商品", value: products.length },
            { label: "今日营收", value: "¥0" },
            { label: "加量中", value: 0 },
            { label: "待淘汰", value: 0 },
          ]}
          recentActions={[]}
        />
      }
      reviewView={<ProductsReviewView products={products} onAddProduct={handleAddProduct} />}
    />
  );
}
