"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot } from "lucide-react";
import { PanelSection } from "./panel-section";
import type { Agent } from "@/lib/types";

interface AgentsListProps {
  agents: Agent[];
  currentAgent: string;
}

export function AgentsList({ agents, currentAgent }: AgentsListProps) {
  const activeAgent = agents.find((a) => a.name === currentAgent);
  return (
    <PanelSection
      title="Available Agents"
      icon={<Bot className="h-4 w-4 text-brand" />}
    >
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
        {agents.map((agent) => (
          <Card
            key={agent.name}
            className={`border border-border-subtle bg-white/80 backdrop-blur transition-colors duration-200 ${
              agent.name === currentAgent ||
              activeAgent?.handoffs.includes(agent.name)
                ? "hover:border-brand/40"
                : "pointer-events-none cursor-not-allowed opacity-50 grayscale"
            } ${
              agent.name === currentAgent
                ? "border-brand/40 shadow-soft ring-1 ring-brand/30"
                : ""
            }`}
          >
            <CardHeader className="p-3 pb-1">
              <CardTitle className="flex items-center text-sm font-semibold text-slate-800">
                {agent.name}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-1">
              <p className="text-xs text-slate-500">
                {agent.description}
              </p>
              {agent.name === currentAgent && (
                <Badge className="mt-2 bg-brand text-brand-foreground">
                  Active
                </Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </PanelSection>
  );
}
