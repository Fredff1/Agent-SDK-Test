"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";

interface SeatMapProps {
    onSeatSelect: (seatNumber: string) => void;
    selectedSeat?: string;
}

// Define seat layout for a typical narrow-body aircraft
const SEAT_LAYOUT = {
    business: { rows: [1, 2, 3, 4], seatsPerRow: ['A', 'B', 'C', 'D'] },
    economyPlus: { rows: [5, 6, 7, 8], seatsPerRow: ['A', 'B', 'C', 'D', 'E', 'F'] },
    economy: {
        rows: Array.from({ length: 16 }, (_, i) => i + 9), // rows 9-24
        seatsPerRow: ['A', 'B', 'C', 'D', 'E', 'F']
    }
};

const OCCUPIED_SEATS = new Set([
    '1A', '2B', '3C', '5A', '5F', '7B', '7E', '9A', '9F', '10C', '10D',
    '12A', '12F', '14B', '14E', '16A', '16F', '18C', '18D', '20A', '20F',
    '22B', '22E', '24A', '24F'
]);

const EXIT_ROWS = new Set([4, 16]);

export function SeatMap({ onSeatSelect, selectedSeat }: SeatMapProps) {
    const getSeatStatus = (seatNumber: string) => {
        if (OCCUPIED_SEATS.has(seatNumber)) return 'occupied';
        if (selectedSeat === seatNumber) return 'selected';
        return 'available';
    };

    const getSeatColor = (status: string, isExit: boolean) => {
        // Available = emerald, Occupied = gray, Exit Row = yellow (pastel)
        switch (status) {
            case 'occupied':
                return 'bg-slate-200 text-slate-400 cursor-not-allowed';
            case 'selected':
                return 'bg-brand text-brand-foreground cursor-pointer hover:opacity-90';
            case 'available':
                return isExit
                    ? 'bg-amber-100 hover:bg-amber-200 cursor-pointer border-amber-200'
                    : 'bg-white hover:bg-brand/10 cursor-pointer border-brand/30';
            default:
                return 'bg-white';
        }
    };

    const renderSeatSection = (title: string, config: typeof SEAT_LAYOUT.business, className: string) => (
        <div className={`mb-6 ${className}`}>
            <h4 className="mb-2 text-center text-sm font-semibold text-slate-700">{title}</h4>
            <div className="space-y-1">
                {config.rows.map(row => {
                    const isExitRow = EXIT_ROWS.has(row);
                    return (
                        <div key={row} className="flex items-center justify-center gap-1">
                            <span className="mr-2 w-6 text-right text-xs text-slate-500">{row}</span>
                            <div className="flex gap-1">
                                {config.seatsPerRow.slice(0, Math.ceil(config.seatsPerRow.length / 2)).map(letter => {
                                    const seatNumber = `${row}${letter}`;
                                    const status = getSeatStatus(seatNumber);
                                    return (
                                        <button
                                            key={seatNumber}
                                            className={`h-8 w-8 rounded border text-xs font-medium transition-colors ${getSeatColor(status, isExitRow)}`}
                                            onClick={() => status === 'available' && onSeatSelect(seatNumber)}
                                            disabled={status === 'occupied'}
                                            title={`Seat ${seatNumber}${isExitRow ? ' (Exit Row)' : ''}${status === 'occupied' ? ' - Occupied' : ''}`}
                                        >
                                            {letter}
                                        </button>
                                    );
                                })}
                            </div>
                            <div className="w-4" /> {/* Aisle */}
                            <div className="flex gap-1">
                                {config.seatsPerRow.slice(Math.ceil(config.seatsPerRow.length / 2)).map(letter => {
                                    const seatNumber = `${row}${letter}`;
                                    const status = getSeatStatus(seatNumber);
                                    return (
                                        <button
                                            key={seatNumber}
                                            className={`h-8 w-8 rounded border text-xs font-medium transition-colors ${getSeatColor(status, isExitRow)}`}
                                            onClick={() => status === 'available' && onSeatSelect(seatNumber)}
                                            disabled={status === 'occupied'}
                                            title={`Seat ${seatNumber}${isExitRow ? ' (Exit Row)' : ''}${status === 'occupied' ? ' - Occupied' : ''}`}
                                        >
                                            {letter}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );

    return (
        <Card className="mx-auto my-4 w-full max-w-md border-border-subtle bg-white/90 shadow-soft">
            <CardContent className="p-4">
                <div className="text-center mb-4">
                    <h3 className="mb-2 text-lg font-semibold text-slate-800">Select Your Seat</h3>
                    <div className="flex justify-center gap-4 text-xs text-slate-600">
                        <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded border border-brand/30 bg-white"></div>
                            <span>Available</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded bg-slate-200"></div>
                            <span>Occupied</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded border border-amber-200 bg-amber-100"></div>
                            <span>Exit Row</span>
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    {renderSeatSection("Business Class", SEAT_LAYOUT.business, "border-b pb-4")}
                    {renderSeatSection("Economy Plus", SEAT_LAYOUT.economyPlus, "border-b pb-4")}
                    {renderSeatSection("Economy", SEAT_LAYOUT.economy, "")}
                </div>

                {selectedSeat && (
                    <div className="mt-4 rounded-lg bg-brand/10 p-3 text-center">
                        <p className="text-sm font-medium text-slate-800">
                            Selected: Seat {selectedSeat}
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
} 
