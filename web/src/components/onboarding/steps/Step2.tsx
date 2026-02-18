"use client";

import { useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useOnboardingStore } from "@/lib/onboarding-store";

const defaultValues = [
  { id: "autonomy", label: "Freedom", emoji: "🦅" },
  { id: "security", label: "Security", emoji: "🛡️" },
  { id: "achievement", label: "Achievement", emoji: "🏔️" },
  { id: "intimacy", label: "Depth", emoji: "🌊" },
  { id: "novelty", label: "Adventure", emoji: "🧭" },
  { id: "stability", label: "Stability", emoji: "⚓" },
  { id: "power", label: "Influence", emoji: "👑" },
  { id: "belonging", label: "Belonging", emoji: "🤝" },
];

function SortableItem({ id, label, emoji }: { id: string; label: string; emoji: string }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`flex items-center gap-4 rounded-lg border border-[#162638] px-5 py-4 cursor-grab active:cursor-grabbing transition-all ${
        isDragging ? "bg-[#00c8ff]/10 border-[#00c8ff]/50 shadow-lg z-10" : "bg-transparent hover:border-[#00c8ff]/30"
      }`}
    >
      <span className="text-xl">{emoji}</span>
      <span className="font-[family-name:var(--font-space-mono)] text-sm text-[#e8f4ff]">
        {label}
      </span>
      <span className="ml-auto text-[#e8f4ff]/30">⠿</span>
    </div>
  );
}

export function Step2() {
  const { setAnswer, nextStep } = useOnboardingStore();
  const [items, setItems] = useState(defaultValues);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setItems((prev) => {
        const oldIndex = prev.findIndex((i) => i.id === active.id);
        const newIndex = prev.findIndex((i) => i.id === over.id);
        return arrayMove(prev, oldIndex, newIndex);
      });
    }
  }

  function handleConfirm() {
    setAnswer(
      "valueRanking",
      items.map((i) => i.id)
    );
    nextStep();
  }

  return (
    <div className="w-full max-w-md">
      <h2 className="font-[family-name:var(--font-syne)] text-[28px] font-bold leading-tight text-[#e8f4ff] text-center mb-8">
        Drag these into your order. Most important at the top.
      </h2>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={items} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {items.map((item) => (
              <SortableItem
                key={item.id}
                id={item.id}
                label={item.label}
                emoji={item.emoji}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      <button
        onClick={handleConfirm}
        className="mt-8 w-full rounded-lg bg-[#00c8ff] py-3 text-sm font-semibold text-[#020408] transition-colors hover:bg-[#00c8ff]/90"
      >
        This is my order →
      </button>
    </div>
  );
}
