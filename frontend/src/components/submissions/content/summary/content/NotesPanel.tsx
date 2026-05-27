"use client";

import { useState } from "react";
import { User, Plus } from "lucide-react";
import { useDsiStore } from "@/store/dsiStore";
import { formatText } from "@/lib/format";
import { NoData } from "@/components/base/content/primatives";

interface StoredNote {
  note?: string;
  text?: string;
  source?: string;
}

export default function NotesPanel() {
  const { activeVersion, addNote } = useDsiStore();
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
      <div className="flex gap-1 justify-between">
        
        <input
          type="text"
          value={newNoteText}
          onChange={(e) => setNewNoteText(e.target.value)}
          placeholder="Add a note..."   
          className="generate-light-inputbox w-[95%]"
          onKeyDown={(e) => e.key === "Enter" && handleAddNote()}
          disabled={isAddingNote}
        />
        
        <button
          onClick={handleAddNote}
          disabled={!newNoteText.trim() || isAddingNote}
          className="generate-light-actionbutton"
        >{isAddingNote ? "Saving..." : "Add"}
        </button>

      </div>

      {notes.length === 0 ? (
        <NoData className="mt-2" message="No notes recorded yet. Add one above." />
      ) : (
        
        
        <div className="mt-2 items-center">
          {[...notes].reverse().map((note, i) => {
            const text = typeof note === "object" ? note.note ?? note.text : note;
            const source = typeof note === "object" ? note.source ?? "System" : "System";
            return (
              <div
                key={i}
                className="flex pt-1 pr-2 text-sm text-wrap"
              >
                <span className="flex w-[10%]"> {formatText(source,"capitalize")}</span>
                <p className="flex pl-generate-pad">{text}</p>
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
  const { activeVersion } = useDsiStore();
  const n = activeVersion?.notes?.length ?? 0;
  return `${base} (${n})`;
}
