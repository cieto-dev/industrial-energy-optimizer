import { industrialModules } from "../../../data/industrial-intelligence";
import ClientPage from "./ClientPage";

export function generateStaticParams() {
  return industrialModules.map((m) => ({
    moduleId: m.id,
  }));
}

export default function ModulePage() {
  return <ClientPage />;
}
