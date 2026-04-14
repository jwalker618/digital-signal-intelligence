"use client";

/**
 * Notes panel — inline add + persisted list. Body content for a
 * StandardCard (titled "Notes (N)"). The count should be surfaced on the
 * StandardCard title by the caller if desired.
 */

import { useState } from "react";
import { User, Plus } from "lucide-react";
import { useDsiStore } from "@/store/dsiStore";

interface StoredNote {
  note?: string;
  text?: string;
  source?: string;
}

export default function NotesPanel() {
  const { activeVersion, addNote } = useDsiStore() as any;
  const notes: Array<StoredNote | string> = activeVersion?.notes ?? [];

  const [newNoteText, setNewNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);

  const handleAddNote = async () => {
    if (!newNoteText.trim() || !activeVersion?.version_code) return;
    setIsAddingNote(true);
    await addNote(activeVersion.version_code, newNoteText.trim(), "underwriter");
    setNewNoteText("");
    setIsAddingNote(false);
  };

  return (
    <>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newNoteText}
          onChange={(e) => setNewNoteText(e.target.value)}
          placeholder="Add a note..."
          className="
            flex-1
            bg-dsi-contrast-analysis
            border-1 border-dsi-contrast-analysis/30
            pr-dsi-pad pl-dsi-pad ml-2 py-2
            text-sm
            hover:text-dsi-selected
            hover:border-dsi-outline"
          onKeyDown={(e) => e.key === "Enter" && handleAddNote()}
          disabled={isAddingNote}
        />
        <button
          onClick={handleAddNote}
          disabled={!newNoteText.trim() || isAddingNote}
          className="
            text-dsi-analysis text-sm
            gap-1
            bg-dsi-contrast-background
            hover:bg-dsi-selected
            pr-dsi-pad pl-dsi-pad mr-2
            flex items-center"
        >
          {isAddingNote ? "Saving..." : "Add"} <Plus className="icon" />
        </button>
      </div>

      {notes.length === 0 ? (
        <p className="dsi-user-message">No notes recorded yet. Add one above.</p>
      ) : (
        <div className="space-y-2 max-h-[300px] overflow-y-auto no-scrollbar">
          {[...notes].reverse().map((note, i) => {
            const text = typeof note === "object" ? note.note ?? note.text : note;
            const source = typeof note === "object" ? note.source ?? "System" : "System";
            return (
              <div
                key={i}
                className="bg-dsi-background/30 rounded-lg p-3 border border-dsi-outline/10 text-wrap"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] opacity-50 flex items-center gap-1">
                    <User className="w-2.5 h-2.5" /> {source}
                  </span>
                </div>
                <p className="text-xs leading-relaxed">{text}</p>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

/** Caller helper — returns `Notes (N)` for use as the StandardCard title. */
export function useNotesCountTitle(base = "Notes"): string {
  const { activeVersion } = useDsiStore() as any;
  const n = activeVersion?.notes?.length ?? 0;
  return `${base} (${n})`;
}
