import React from 'react';
import { X, BookOpen, ShieldCheck, Tag, FileText } from 'lucide-react';
import { SourceChunk } from '../types';

interface PassageModalProps {
  chunk: SourceChunk | null;
  onClose: () => void;
}

export const PassageModal: React.FC<PassageModalProps> = ({ chunk, onClose }) => {
  if (!chunk) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-5 h-5 text-sky-600" />
            <h3 className="font-semibold text-slate-800 text-base">Retrieved Clinical Evidence Passage</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Metadata bar */}
        <div className="px-6 py-3 bg-sky-50/50 border-b border-sky-100/60 flex flex-wrap gap-2 text-xs">
          <span className="font-semibold text-slate-700">{chunk.document}</span>
          {chunk.version && (
            <span className="bg-white text-slate-600 px-2 py-0.5 rounded border border-slate-200">
              v{chunk.version}
            </span>
          )}
          {chunk.page && (
            <span className="bg-white text-slate-600 px-2 py-0.5 rounded border border-slate-200">
              Page {chunk.page}
            </span>
          )}
          {chunk.section && (
            <span className="bg-white text-sky-700 px-2 py-0.5 rounded border border-sky-200 font-medium">
              Sec: {chunk.section}
            </span>
          )}
          {chunk.similarity_score !== undefined && (
            <span className="ml-auto text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-mono font-semibold border border-emerald-200">
              Score: {chunk.similarity_score.toFixed(4)}
            </span>
          )}
        </div>

        {/* Content Passage */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verbatim Clinical Passage</span>
            <div className="mt-2 p-4 bg-slate-50 rounded-lg border border-slate-200 text-slate-800 text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {chunk.chunk_text}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs text-slate-500 pt-2 border-t border-slate-100">
            <div>
              <span className="font-medium text-slate-700">Chunk Type: </span>
              <span className="capitalize">{chunk.chunk_type || 'text'}</span>
            </div>
            <div>
              <span className="font-medium text-slate-700">Department: </span>
              <span>{chunk.department || 'General Medicine'}</span>
            </div>
            {chunk.effective_date && (
              <div>
                <span className="font-medium text-slate-700">Effective Date: </span>
                <span>{chunk.effective_date}</span>
              </div>
            )}
            <div>
              <span className="font-medium text-slate-700">Database Chunk ID: </span>
              <span className="font-mono">{chunk.chunk_id}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-sm font-medium rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
