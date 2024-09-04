import GraphChat from "@/components/GraphChat";
import SimpleChat from "@/components/SimpleChat";

export default function Home() {
  return (
    <main className="flex h-screen p-24 gap-4">
      <div className="flex flex-col flex-1">
        <h2>Simple Chat</h2>
        <div className="flex-1 max-h-[calc(100%-20px)]">
          <SimpleChat />
        </div>
      </div>
      <div className="flex flex-col flex-1 ">
        <h2>Graph Chat</h2>
        <div className="flex-1 max-h-[calc(100%-20px)]">
          <GraphChat />
        </div>
      </div>
    </main>
  );
}
