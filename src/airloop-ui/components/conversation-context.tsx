"use client";

import { PanelSection } from "./panel-section";
import { Card, CardContent } from "@/components/ui/card";
import { BookText } from "lucide-react";

interface ConversationContextProps {
  context: {
    order_id?: number;
    passenger_name?: string;
    confirmation_number?: string;
    seat_number?: string;
    flight_number?: string;
    account_number?: string;
    meal_selection?: string | null;
  };
}

export function ConversationContext({ context }: ConversationContextProps) {
  const filteredEntries = Object.entries(context).filter(
    ([key, value]) => key !== "available_meals" && key !== "meal_preference" && key != "conversation_state"
  );

  return (
    <PanelSection
      title="Conversation Context"
      icon={<BookText className="h-4 w-4 text-brand" />}
    >
      <Card className="border-border-subtle bg-white/80 shadow-soft backdrop-blur">
        <CardContent className="p-3">
          <div className="grid grid-cols-2 gap-2">
            {filteredEntries.map(([key, value]) => (
              <div
                key={key}
                className="flex items-center gap-2 rounded-md border border-border-subtle bg-white/90 p-2 transition-colors duration-200 hover:border-brand/30"
              >
                <div className="h-2 w-2 rounded-full bg-brand"></div>
                <div className="text-xs">
                  <span className="text-slate-500">{key}:</span>{" "}
                  <span
                    className={
                      value
                        ? "text-slate-800"
                        : "italic text-slate-400"
                    }
                  >
                    {value || "null"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </PanelSection>
  );
}
