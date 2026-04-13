"use client";

import React from "react";
import { X, AlertTriangle } from "lucide-react";

interface DeleteModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    userName?: string;
}

export default function DeleteModal({ isOpen, onClose, onConfirm, userName }: DeleteModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <div
                className="absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300 animate-in fade-in"
                onClick={onClose}
            />
            <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl ring-1 ring-black/5 transform transition-all animate-in zoom-in-95 fade-in duration-200 overflow-hidden">
                {/* Icon Header */}
                <div className="flex flex-col items-center pt-8 pb-4 px-6">
                    <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
                        <AlertTriangle className="w-8 h-8 text-red-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 text-center">
                        ¿Eliminar usuario?
                    </h3>
                    <p className="text-gray-500 text-center mt-2 text-sm">
                        {userName ? (
                            <>
                                Estás a punto de eliminar a <span className="font-semibold text-gray-700">{userName}</span>. Esta acción no se puede deshacer.
                            </>
                        ) : (
                            "Esta acción no se puede deshacer."
                        )}
                    </p>
                </div>

                {/* Actions */}
                <div className="flex gap-3 p-6 bg-gray-50 border-t border-gray-100">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2.5 text-sm font-semibold text-gray-700 bg-white ring-1 ring-gray-200 hover:bg-gray-50 rounded-xl transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={() => {
                            onConfirm();
                            onClose();
                        }}
                        className="flex-1 px-4 py-2.5 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-xl shadow-md shadow-red-500/25 active:scale-95 transition-all"
                    >
                        Sí, eliminar
                    </button>
                </div>
            </div>
        </div>
    );
}
