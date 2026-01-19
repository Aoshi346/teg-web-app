import React from "react";
import { Project } from "@/lib/data/mockData";
import { FileText, BookOpen, Clock, Calendar, CheckCircle, XCircle } from "lucide-react";

interface TrackingTableProps {
    items: Project[];
    onReview?: (project: Project) => void;
}

const TrackingTable: React.FC<TrackingTableProps> = ({ items, onReview }) => {
    if (items.length === 0) {
        return (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900">
                    Todo al día
                </h3>
                <p className="text-gray-500 mt-1">
                    No hay evaluaciones pendientes en este momento.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 font-medium">
                            <th className="px-6 py-4">Proyecto / Tesis</th>
                            <th className="px-6 py-4">Estudiante</th>
                            <th className="px-6 py-4">Tipo</th>
                            <th className="px-6 py-4">Fecha Entrega</th>
                            <th className="px-6 py-4">Estado</th>
                            <th className="px-6 py-4 text-right">Acción</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {items.map((item) => {
                            const isTesis = "stage1Passed" in item;
                            const typeLabel = isTesis ? "TEG" : "PTEG";
                            const typeColor = isTesis
                                ? "bg-purple-100 text-purple-700"
                                : "bg-blue-100 text-blue-700";
                            const Icon = isTesis ? BookOpen : FileText;

                            return (
                                <tr
                                    key={`${typeLabel}-${item.id}`}
                                    className="hover:bg-gray-50/50 transition-colors"
                                >
                                    <td className="px-6 py-4">
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-gray-100 rounded-lg flex-shrink-0 mt-0.5">
                                                <Icon className="w-5 h-5 text-gray-600" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-gray-900 line-clamp-1">
                                                    {item.title}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                                                    Tutor: {item.advisor}
                                                </p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-gray-800">
                                        {item.student}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span
                                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${typeColor}`}
                                        >
                                            {typeLabel}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-600">
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-gray-400" />
                                            {item.submittedDate}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700 border border-amber-200">
                                            <Clock className="w-3.5 h-3.5" />
                                            Pendiente
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => onReview?.(item)}
                                            className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 shadow-sm hover:shadow transition-all duration-200"
                                        >
                                            Revisar
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TrackingTable;
