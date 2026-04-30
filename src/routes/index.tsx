import { createFileRoute } from "@tanstack/react-router";
import PrologIDE from "@/components/PrologIDE";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "PrologLab - محرر برولوج تفاعلي على الويب" },
      { name: "description", content: "بيئة برمجة Prolog تفاعلية على المتصفح لكتابة وتنفيذ البرامج المنطقية مع أمثلة جاهزة" },
    ],
  }),
});

function Index() {
  return <PrologIDE />;
}
