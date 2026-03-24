"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkles, Loader2 } from "lucide-react";
import { login, register } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Login state
  const [loginPhone, setLoginPhone] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register state
  const [regPhone, setRegPhone] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regInviteCode, setRegInviteCode] = useState("");

  const handleLogin = async () => {
    if (!loginPhone || !loginPassword) {
      setError("请输入手机号和密码");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await login(loginPhone, loginPassword);
      router.push("/cockpit");
    } catch (e: any) {
      setError(e.message || "登录失败");
    }
    setLoading(false);
  };

  const handleRegister = async () => {
    if (!regPhone || !regPassword) {
      setError("请输入手机号和密码");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await register(regPhone, regPassword, regInviteCode);
      router.push("/onboarding");
    } catch (e: any) {
      setError(e.message || "注册失败");
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen">
      {/* Left - Brand */}
      <div className="hidden lg:flex lg:w-[55%] bg-gradient-to-br from-indigo-600 via-indigo-500 to-blue-500 text-white flex-col justify-center px-16">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 text-xl font-bold">商</div>
          <span className="text-2xl font-bold tracking-wide">商探AI</span>
        </div>
        <h1 className="text-4xl font-bold leading-tight">
          AI 替你做电商
          <br />
          你只管收钱
        </h1>
        <p className="mt-4 text-lg text-white/80 max-w-md">
          全自动电商操盘系统。从选品到发货，AI 替代5人团队全自动运转。
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          {["趋势发现", "市场评估", "供应链匹配", "内容工厂", "自动发布", "AI客服", "数据分析"].map((m) => (
            <span key={m} className="rounded-full bg-white/15 px-3 py-1 text-xs">{m}</span>
          ))}
        </div>
      </div>

      {/* Right - Form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">商</div>
            <span className="text-lg font-bold">商探AI</span>
          </div>

          {error && (
            <div className="mb-4 text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <Tabs defaultValue="login">
            <TabsList className="w-full">
              <TabsTrigger value="login" className="flex-1">登录</TabsTrigger>
              <TabsTrigger value="register" className="flex-1">注册</TabsTrigger>
            </TabsList>

            <TabsContent value="login" className="mt-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">手机号</label>
                <Input
                  placeholder="输入手机号"
                  value={loginPhone}
                  onChange={(e) => setLoginPhone(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">密码</label>
                <Input
                  placeholder="输入密码"
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                />
              </div>
              <Button className="w-full" onClick={handleLogin} disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                登录
              </Button>
            </TabsContent>

            <TabsContent value="register" className="mt-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">手机号</label>
                <Input
                  placeholder="输入手机号"
                  value={regPhone}
                  onChange={(e) => setRegPhone(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">密码</label>
                <Input
                  placeholder="设置密码（6位以上）"
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">邀请码（选填）</label>
                <Input
                  placeholder="输入邀请码"
                  value={regInviteCode}
                  onChange={(e) => setRegInviteCode(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={handleRegister} disabled={loading}>
                {loading && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                <Sparkles className="h-4 w-4 mr-2" />注册并领取 3000 运营力
              </Button>
              <p className="text-[10px] text-center text-muted-foreground">
                注册即表示同意《服务协议》和《隐私政策》
              </p>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
