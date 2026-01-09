"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, CheckCircle, XCircle } from "lucide-react";
import { PanelSection } from "./panel-section";
import type { GuardrailCheck } from "@/lib/types";

interface GuardrailsProps {
  guardrails: GuardrailCheck[];
  inputGuardrails: string[];
}

export function Guardrails({ guardrails, inputGuardrails }: GuardrailsProps) {
  const guardrailNameMap: Record<string, string> = {
    relevance_guardrail: "Relevance Guardrail",
    jailbreak_guardrail: "Jailbreak Guardrail",
    "Relevance Guardrail": "Relevance Guardrail",
    "Jailbreak Guardrail": "Jailbreak Guardrail",
  };

  const guardrailDescriptionMap: Record<string, string> = {
    "Relevance Guardrail": "Ensure messages are relevant to airline support",
    "Jailbreak Guardrail":
      "Detect and block attempts to bypass or override system instructions",
  };

  const extractGuardrailName = (rawName: string): string =>
    guardrailNameMap[rawName] ?? rawName;

  const uniqueInputs = Array.from(new Set(inputGuardrails));

  const guardrailsToShow: GuardrailCheck[] = uniqueInputs.map((rawName) => {
    const existing = guardrails.find((gr) => gr.name === rawName);
    if (existing) {
      return existing;
    }
    return {
      id: rawName,
      name: rawName,
      input: "",
      reasoning: "",
      passed: false,
      timestamp: new Date(),
    };
  });

  return (
    <PanelSection
      title="Guardrails"
      icon={<Shield className="h-4 w-4 text-brand" />}
    >
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
        {guardrailsToShow.map((gr) => (
          <Card
            key={gr.id}
            className={`border border-border-subtle bg-white/80 backdrop-blur transition-colors duration-200 ${
              !gr.input ? "opacity-60" : "hover:border-brand/30"
            }`}
          >
            <CardHeader className="p-3 pb-1">
              <CardTitle className="text-sm font-semibold text-slate-800">
                {extractGuardrailName(gr.name)}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-1">
              <p className="mb-1 text-xs text-slate-500">
                {(() => {
                  const title = extractGuardrailName(gr.name);
                  return guardrailDescriptionMap[title] ?? gr.input;
                })()}
              </p>
              <div className="flex text-xs">
                {!gr.input || gr.passed ? (
                  <Badge className="mt-2 flex items-center bg-emerald-500 px-2 py-1 text-white">
                    <CheckCircle className="mr-1 h-4 w-4 text-white" />
                    Passed
                  </Badge>
                ) : (
                  <Badge className="mt-2 flex items-center bg-red-500 px-2 py-1 text-white">
                    <XCircle className="mr-1 h-4 w-4 text-white" />
                    Failed
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </PanelSection>
  );
}
