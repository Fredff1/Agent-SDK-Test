"use client";

import { PanelSection } from "./panel-section";
import { Card, CardContent } from "@/components/ui/card";
import { ReceiptText } from "lucide-react";

type Order = {
  id: number;
  confirmation_number: string;
  flight_number: string;
  seat_number: number;
  meal_selection?: string | null;
};

interface OrderPanelProps {
  orders: Order[];
  isLoading: boolean;
  error?: string;
  onCreateOrder: () => void;
  onRefresh: () => void;
}

export function OrderPanel({
  orders,
  isLoading,
  error,
  onCreateOrder,
  onRefresh,
}: OrderPanelProps) {
  return (
    <PanelSection
      title="Orders"
      icon={<ReceiptText className="h-4 w-4 text-brand" />}
    >
      <Card className="border-border-subtle bg-white/80 shadow-soft backdrop-blur">
        <CardContent className="space-y-3 p-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-full border border-border-subtle bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors duration-200 hover:border-brand/40 hover:text-slate-900"
              onClick={onCreateOrder}
            >
              + New order
            </button>
            <button
              type="button"
              className="rounded-full border border-border-subtle px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-600 transition-colors duration-200 hover:border-brand/40 hover:text-slate-900"
              onClick={onRefresh}
            >
              Refresh
            </button>
          </div>
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-xs text-red-600">
              {error}
            </div>
          )}
          {isLoading ? (
            <div className="text-xs text-slate-500">Loading orders...</div>
          ) : orders.length === 0 ? (
            <div className="text-xs text-slate-500">No orders yet.</div>
          ) : (
            <div className="space-y-2">
              {orders.map((order) => (
                <div
                  key={order.id}
                  className="rounded-lg border border-border-subtle bg-white/90 p-2 text-xs text-slate-700"
                >
                  <div className="font-semibold text-slate-800">
                    {order.confirmation_number}
                  </div>
                  <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span>Flight: {order.flight_number}</span>
                    <span>Seat: {order.seat_number}</span>
                    {order.meal_selection && <span>Meal: {order.meal_selection}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </PanelSection>
  );
}
