import { useMemo, useState } from "react";
import { BookOpen, Plus } from "lucide-react";
import { api } from "@/api/client";
import { ConfirmationDialog } from "@/components/shared/ConfirmationDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { SearchBar } from "@/components/shared/SearchBar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { useToast } from "@/hooks/toast-context";
import type { KnowledgeEntry, KnowledgeVersion } from "@/types";

export function KnowledgePage({
  businessId,
  entries,
  loading,
  onReload,
}: {
  businessId: string;
  entries: KnowledgeEntry[];
  loading: boolean;
  onReload: () => Promise<void>;
}) {
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [editing, setEditing] = useState<KnowledgeEntry | null>(null);
  const [creating, setCreating] = useState(false);
  const [draft, setDraft] = useState({ category: "general", question: "", answer: "", active: true });
  const [pendingDelete, setPendingDelete] = useState<KnowledgeEntry | null>(null);
  const [busy, setBusy] = useState(false);
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkText, setBulkText] = useState("");
  const [versions, setVersions] = useState<KnowledgeVersion[]>([]);

  const categories = useMemo(
    () => ["all", ...new Set(entries.map((entry) => entry.category))],
    [entries],
  );

  const filtered = entries.filter((entry) => {
    const matchesCategory = category === "all" || entry.category === category;
    const q = query.trim().toLowerCase();
    const matchesQuery =
      !q ||
      entry.question.toLowerCase().includes(q) ||
      entry.answer.toLowerCase().includes(q) ||
      entry.category.toLowerCase().includes(q);
    return matchesCategory && matchesQuery;
  });

  const openCreate = () => {
    setDraft({ category: "general", question: "", answer: "", active: true });
    setCreating(true);
  };

  const openEdit = (entry: KnowledgeEntry) => {
    setEditing(entry);
    setDraft({
      category: entry.category,
      question: entry.question,
      answer: entry.answer,
      active: entry.active,
    });
  };

  const save = async () => {
    if (!draft.question.trim() || !draft.answer.trim()) {
      toast({ title: "Missing fields", description: "Question and answer are required.", variant: "danger" });
      return;
    }
    setBusy(true);
    try {
      if (editing) {
        await api.updateKnowledge(editing.id, draft);
        toast({ title: "Entry updated" });
      } else {
        await api.addKnowledge(businessId, draft);
        toast({ title: "Entry created" });
      }
      setCreating(false);
      setEditing(null);
      await onReload();
    } catch (err) {
      toast({
        title: "Save failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "danger",
      });
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!pendingDelete) return;
    setBusy(true);
    try {
      await api.deleteKnowledge(pendingDelete.id);
      toast({ title: "Entry deleted" });
      setPendingDelete(null);
      await onReload();
    } catch (err) {
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "danger",
      });
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-80" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Base"
        description="Curate answers your voice agent uses during live conversations."
        actions={
          <div className="flex gap-2"><Button variant="outline" onClick={() => setBulkOpen(true)}>Bulk import</Button><Button onClick={openCreate}><Plus className="h-4 w-4" />Add entry</Button></div>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <SearchBar value={query} onChange={setQuery} className="sm:max-w-sm" placeholder="Search knowledge…" />
        <div className="flex flex-wrap gap-2">
          {categories.map((item) => (
            <Button
              key={item}
              size="sm"
              variant={category === item ? "default" : "outline"}
              onClick={() => setCategory(item)}
              className="capitalize"
            >
              {item}
            </Button>
          ))}
        </div>
      </div>

      {!filtered.length ? (
        <EmptyState
          icon={BookOpen}
          title="No knowledge entries"
          description="Add FAQs and service answers so the receptionist can respond accurately."
          actionLabel="Add entry"
          onAction={openCreate}
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b border-border bg-muted/40 text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Question</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((entry) => (
                    <tr key={entry.id} className="border-b border-border/70">
                      <td className="px-4 py-4">
                        <div className="font-medium">{entry.question}</div>
                        <div className="mt-1 line-clamp-2 max-w-xl text-muted-foreground">{entry.answer}</div>
                      </td>
                      <td className="px-4 py-4 capitalize">{entry.category}</td>
                      <td className="px-4 py-4">
                        <Badge variant={entry.active ? "success" : "secondary"}>
                          {entry.active ? "Active" : "Disabled"}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => openEdit(entry)}>
                            Edit
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => void api.knowledgeVersions(entry.id).then(setVersions)}>
                            History
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={async () => {
                              await api.updateKnowledge(entry.id, { active: !entry.active });
                              await onReload();
                            }}
                          >
                            {entry.active ? "Disable" : "Enable"}
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => setPendingDelete(entry)}>
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <Dialog
        open={creating || !!editing}
        onOpenChange={(open) => {
          if (!open) {
            setCreating(false);
            setEditing(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit knowledge entry" : "New knowledge entry"}</DialogTitle>
            <DialogDescription>These answers feed receptionist responses during live calls.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="kb-category">Category</Label>
              <Input
                id="kb-category"
                value={draft.category}
                onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="kb-question">Question</Label>
              <Input
                id="kb-question"
                value={draft.question}
                onChange={(event) => setDraft((current) => ({ ...current, question: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="kb-answer">Answer</Label>
              <Textarea
                id="kb-answer"
                value={draft.answer}
                onChange={(event) => setDraft((current) => ({ ...current, answer: event.target.value }))}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setCreating(false);
                  setEditing(null);
                }}
              >
                Cancel
              </Button>
              <Button onClick={() => void save()} disabled={busy}>
                {busy ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <ConfirmationDialog
        open={!!pendingDelete}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title="Delete knowledge entry?"
        description="This removes the answer from your receptionist knowledge base. This cannot be undone."
        confirmLabel="Delete"
        danger
        loading={busy}
        onConfirm={() => void remove()}
      />
      <Dialog open={bulkOpen} onOpenChange={setBulkOpen}><DialogContent><DialogHeader><DialogTitle>Bulk import knowledge</DialogTitle><DialogDescription>Paste JSON lines ({`{"question":"…","answer":"…","category":"general"}`}) or Q/A lines.</DialogDescription></DialogHeader><Textarea className="min-h-48 font-mono" value={bulkText} onChange={(event) => setBulkText(event.target.value)} placeholder={'{"question":"What are your hours?","answer":"Mon–Fri, 9–5","category":"hours"}'} /><div className="flex justify-end gap-2"><Button variant="outline" onClick={() => setBulkOpen(false)}>Cancel</Button><Button onClick={async () => { const entries = bulkText.split("\n").filter(Boolean).map((line) => { try { const item: unknown = JSON.parse(line); if (typeof item === "object" && item !== null && "question" in item && "answer" in item) { const record = item as Record<string, unknown>; return { category: typeof record.category === "string" ? record.category : "general", question: String(record.question), answer: String(record.answer), active: true }; } } catch { const [question, ...answer] = line.split(/\s*[:?]\s*/); return { category: "general", question, answer: answer.join(" "), active: true }; } throw new Error("Invalid import line"); }); await api.bulkKnowledge(businessId, entries); setBulkOpen(false); setBulkText(""); await onReload(); toast({ title: "Knowledge imported" }); }}>Import</Button></div></DialogContent></Dialog>
      <Dialog open={versions.length > 0} onOpenChange={(open) => !open && setVersions([])}><DialogContent><DialogHeader><DialogTitle>Version history</DialogTitle></DialogHeader><div className="max-h-96 space-y-3 overflow-auto">{versions.map((version) => <Card key={version.id}><CardContent className="p-3 text-sm"><div className="font-medium">Version {version.version} · {new Date(version.created_at).toLocaleString()}</div><p className="mt-1 text-muted-foreground">{version.answer}</p></CardContent></Card>)}</div></DialogContent></Dialog>
    </div>
  );
}
