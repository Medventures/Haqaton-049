import { DemoPanel } from "@/components/DemoPanel";

export default function CuratorLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <DemoPanel />
    </>
  );
}
