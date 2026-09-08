"use client";

import { useCallback, useId, useRef, useState } from "react";

interface FileDropzoneProps {
  label: string;
  hint: string;
  /** Accept attribute plus the extensions used to validate a dropped file. */
  accept: string;
  extensions: string[];
  file: File | null;
  onSelect: (file: File | null) => void;
  disabled?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileDropzone({
  label,
  hint,
  accept,
  extensions,
  file,
  onSelect,
  disabled = false,
}: FileDropzoneProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accepts = useCallback(
    (candidate: File) =>
      extensions.some((extension) =>
        candidate.name.toLowerCase().endsWith(extension)
      ),
    [extensions]
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const candidate = files?.[0];
      if (!candidate) return;

      if (!accepts(candidate)) {
        setError(`Expected ${extensions.join(" or ")}.`);
        return;
      }

      setError(null);
      onSelect(candidate);
    },
    [accepts, extensions, onSelect]
  );

  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (!disabled) handleFiles(event.dataTransfer.files);
        }}
        className={`rounded-lg border-2 border-dashed p-6 text-center transition ${
          dragging
            ? "border-slate-900 bg-slate-50"
            : "border-slate-300 bg-white"
        } ${disabled ? "opacity-50" : ""}`}
      >
        <p className="text-sm font-medium">{label}</p>
        <p className="mt-1 text-xs text-slate-500">{hint}</p>

        {file ? (
          <div className="mt-3 flex items-center justify-center gap-2 text-sm">
            <span className="font-medium text-emerald-700">{file.name}</span>
            <span className="text-xs text-slate-500">
              ({formatBytes(file.size)})
            </span>
            <button
              type="button"
              onClick={() => {
                onSelect(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              disabled={disabled}
              className="text-xs text-slate-500 underline underline-offset-2 hover:text-slate-900"
            >
              remove
            </button>
          </div>
        ) : (
          <label
            htmlFor={inputId}
            className={`mt-3 inline-block rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium ${
              disabled ? "cursor-not-allowed" : "cursor-pointer hover:border-slate-900"
            }`}
          >
            Choose a file
          </label>
        )}

        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept={accept}
          disabled={disabled}
          onChange={(event) => handleFiles(event.target.files)}
          className="sr-only"
        />
      </div>

      {error ? <p className="mt-2 text-xs text-rose-700">{error}</p> : null}
    </div>
  );
}
