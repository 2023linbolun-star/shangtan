"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Store, Users, Bell, Plus, Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">设置</h1>
        <p className="text-sm text-muted-foreground mt-1">店铺管理、团队、通知偏好</p>
      </div>

      <Tabs defaultValue="stores">
        <TabsList>
          <TabsTrigger value="stores"><Store className="h-3.5 w-3.5 mr-1" />店铺管理</TabsTrigger>
          <TabsTrigger value="team"><Users className="h-3.5 w-3.5 mr-1" />团队</TabsTrigger>
          <TabsTrigger value="notifications"><Bell className="h-3.5 w-3.5 mr-1" />通知偏好</TabsTrigger>
        </TabsList>

        <TabsContent value="stores" className="mt-4 space-y-4">
          <Button><Plus className="h-4 w-4 mr-2" />添加店铺</Button>
          {[
            { name: "我的抖音店铺", platform: "抖音电商", status: "活跃" },
            { name: "淘宝旗舰店", platform: "淘宝", status: "活跃" },
            { name: "拼多多专卖店", platform: "拼多多", status: "未配置" },
          ].map((store) => (
            <Card key={store.name}>
              <CardContent className="p-4 flex items-center gap-4">
                <Store className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-semibold">{store.name}</p>
                  <p className="text-xs text-muted-foreground">{store.platform}</p>
                </div>
                <Badge variant={store.status === "活跃" ? "default" : "secondary"}>{store.status}</Badge>
                <Button variant="outline" size="sm">编辑</Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="team" className="mt-4 space-y-4">
          <Button><Plus className="h-4 w-4 mr-2" />邀请成员</Button>
          {[
            { name: "我（管理员）", email: "admin@example.com", role: "owner" },
            { name: "运营小张", email: "zhang@example.com", role: "editor" },
          ].map((member) => (
            <Card key={member.name}>
              <CardContent className="p-4 flex items-center gap-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  {member.name[0]}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold">{member.name}</p>
                  <p className="text-xs text-muted-foreground">{member.email}</p>
                </div>
                <Badge variant="secondary">{member.role}</Badge>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="notifications" className="mt-4 space-y-4">
          {[
            { channel: "站内通知", enabled: true },
            { channel: "Telegram Bot", enabled: true },
            { channel: "钉钉 Webhook", enabled: false },
            { channel: "Email", enabled: true },
          ].map((n) => (
            <Card key={n.channel}>
              <CardContent className="p-4 flex items-center gap-4">
                <Bell className="h-5 w-5 text-muted-foreground" />
                <span className="flex-1 text-sm font-medium">{n.channel}</span>
                <Badge variant={n.enabled ? "default" : "secondary"}>{n.enabled ? "已启用" : "未配置"}</Badge>
                <Button variant="outline" size="sm">{n.enabled ? "设置" : "配置"}</Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
