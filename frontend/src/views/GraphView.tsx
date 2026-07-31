import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Graph } from "../api";

interface SimNode {
  id: string;
  title: string;
  kind: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  degree: number;
}

/** Small force-directed layout on canvas — no external libraries. */
function simulate(graph: Graph, width: number, height: number): SimNode[] {
  const nodes: SimNode[] = graph.nodes.map((n, i) => {
    const angle = (i / Math.max(1, graph.nodes.length)) * Math.PI * 2;
    const radius = Math.min(width, height) * 0.32 * (0.6 + ((i * 37) % 40) / 100);
    return {
      ...n,
      x: width / 2 + Math.cos(angle) * radius,
      y: height / 2 + Math.sin(angle) * radius,
      vx: 0,
      vy: 0,
      degree: 0,
    };
  });
  const index = new Map(nodes.map((n) => [n.id, n]));
  const edges = graph.edges
    .map((e) => ({ a: index.get(e.from_id), b: index.get(e.to_id) }))
    .filter((e): e is { a: SimNode; b: SimNode } => Boolean(e.a && e.b));
  edges.forEach(({ a, b }) => {
    a.degree += 1;
    b.degree += 1;
  });

  for (let iter = 0; iter < 260; iter++) {
    const cooling = 1 - iter / 260;
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i], b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const d2 = Math.max(100, dx * dx + dy * dy);
        const force = 2600 / d2;
        const d = Math.sqrt(d2);
        a.vx += (dx / d) * force;
        a.vy += (dy / d) * force;
        b.vx -= (dx / d) * force;
        b.vy -= (dy / d) * force;
      }
    }
    edges.forEach(({ a, b }) => {
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.max(1, Math.hypot(dx, dy));
      const pull = (d - 90) * 0.02;
      a.vx += (dx / d) * pull;
      a.vy += (dy / d) * pull;
      b.vx -= (dx / d) * pull;
      b.vy -= (dy / d) * pull;
    });
    nodes.forEach((n) => {
      n.vx += (width / 2 - n.x) * 0.002;
      n.vy += (height / 2 - n.y) * 0.002;
      n.x += Math.max(-8, Math.min(8, n.vx)) * cooling;
      n.y += Math.max(-8, Math.min(8, n.vy)) * cooling;
      n.vx *= 0.6;
      n.vy *= 0.6;
      n.x = Math.max(30, Math.min(width - 30, n.x));
      n.y = Math.max(30, Math.min(height - 30, n.y));
    });
  }
  return nodes;
}

export default function GraphView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [nodes, setNodes] = useState<SimNode[]>([]);
  const [hovered, setHovered] = useState<SimNode | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.getGraph().then(setGraph).catch(() => setGraph({ nodes: [], edges: [] }));
  }, []);

  useEffect(() => {
    if (!graph || !canvasRef.current) return;
    const rect = canvasRef.current.parentElement!.getBoundingClientRect();
    setNodes(simulate(graph, rect.width, rect.height));
  }, [graph]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !graph) return;
    const rect = canvas.parentElement!.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    const ctx = canvas.getContext("2d")!;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);

    const index = new Map(nodes.map((n) => [n.id, n]));
    const neighbors = new Set<string>();
    if (hovered) {
      graph.edges.forEach((e) => {
        if (e.from_id === hovered.id) neighbors.add(e.to_id);
        if (e.to_id === hovered.id) neighbors.add(e.from_id);
      });
    }

    graph.edges.forEach((e) => {
      const a = index.get(e.from_id), b = index.get(e.to_id);
      if (!a || !b) return;
      const active = hovered && (e.from_id === hovered.id || e.to_id === hovered.id);
      ctx.strokeStyle = active ? "rgba(129,140,248,0.8)" : "rgba(85,97,125,0.35)";
      ctx.lineWidth = active ? 1.6 : 1;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    });

    nodes.forEach((n) => {
      const r = 4 + Math.min(6, n.degree * 1.5);
      const isHover = hovered?.id === n.id;
      const isNeighbor = neighbors.has(n.id);
      const dim = hovered && !isHover && !isNeighbor;
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fillStyle = dim
        ? "rgba(85,97,125,0.4)"
        : n.kind === "daily" ? "#22c55e" : n.kind === "snippet" ? "#f59e0b" : "#818cf8";
      ctx.fill();
      if (isHover) {
        ctx.strokeStyle = "#e4e8f1";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      if (!dim && (isHover || isNeighbor || n.degree >= 1 || nodes.length <= 30)) {
        ctx.fillStyle = dim ? "rgba(154,165,189,0.4)" : "#9aa5bd";
        ctx.font = "11px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(
          n.title.length > 24 ? n.title.slice(0, 23) + "…" : n.title,
          n.x, n.y + r + 12,
        );
      }
    });
  }, [nodes, hovered, graph]);

  const findAt = (e: React.MouseEvent) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    return nodes.find((n) => Math.hypot(n.x - x, n.y - y) < 12) ?? null;
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-ink-800 px-5 py-3">
        <h2 className="text-base font-semibold">Graph</h2>
        <span className="text-xs text-ink-500">
          {graph ? `${graph.nodes.length} notes · ${graph.edges.length} links` : "…"}
        </span>
        <span className="ml-auto flex items-center gap-3 text-[11px] text-ink-500">
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-accent-400" /> note</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ background: "#f59e0b" }} /> snippet</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ background: "#22c55e" }} /> daily</span>
        </span>
      </div>
      <div className="relative flex-1">
        <canvas
          ref={canvasRef}
          onMouseMove={(e) => setHovered(findAt(e))}
          onClick={(e) => {
            const n = findAt(e);
            if (n) navigate(`/notes/${n.id}`);
          }}
          className={hovered ? "cursor-pointer" : undefined}
        />
        {graph && graph.nodes.length === 0 && (
          <p className="absolute inset-0 flex items-center justify-center text-sm text-ink-500">
            No notes yet — the graph grows as you write and [[link]] notes.
          </p>
        )}
      </div>
    </div>
  );
}
