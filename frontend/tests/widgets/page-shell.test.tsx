import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { PageShell } from "@widgets/page-shell/PageShell";
import { PageToolbar } from "@widgets/page-shell/PageToolbar";
import { PageBody } from "@widgets/page-shell/PageBody";
import { SectionHeader } from "@widgets/page-shell/SectionHeader";
import { DataTable } from "@widgets/page-shell/DataTable";
import { StatTile } from "@widgets/page-shell/StatTile";
import { Kbd } from "@widgets/page-shell/Kbd";

describe("PageShell", () => {
  it("renders children", () => {
    render(<PageShell><div>Shell content</div></PageShell>);
    expect(screen.getByText("Shell content")).toBeDefined();
  });
});

describe("PageToolbar", () => {
  it("renders Title, Subtitle, and Actions in expected regions", () => {
    render(
      <PageToolbar>
        <PageToolbar.Title>My Title</PageToolbar.Title>
        <PageToolbar.Subtitle>Sub</PageToolbar.Subtitle>
        <PageToolbar.Actions><button>Act</button></PageToolbar.Actions>
      </PageToolbar>
    );
    expect(screen.getByText("My Title")).toBeDefined();
    expect(screen.getByText("Sub")).toBeDefined();
    expect(screen.getByRole("button", { name: "Act" })).toBeDefined();
  });
});

describe("PageBody", () => {
  it("renders children", () => {
    render(<PageBody><p>Body content</p></PageBody>);
    expect(screen.getByText("Body content")).toBeDefined();
  });
});

describe("SectionHeader", () => {
  it("renders title and action slot", () => {
    render(
      <SectionHeader title="SECCIÓN">
        <SectionHeader.Action href="/test">Ver todos</SectionHeader.Action>
      </SectionHeader>
    );
    expect(screen.getByText("SECCIÓN")).toBeDefined();
    expect(screen.getByText("Ver todos")).toBeDefined();
  });
});

interface Row { id: number; name: string }

const columns = [
  { key: "id", header: "ID", render: (r: Row) => <span>{r.id}</span> },
  { key: "name", header: "Nombre", render: (r: Row) => <span>{r.name}</span> },
];

describe("DataTable", () => {
  it("renders rows from data", () => {
    const data: Row[] = [{ id: 1, name: "Alpha" }, { id: 2, name: "Beta" }];
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText("Alpha")).toBeDefined();
    expect(screen.getByText("Beta")).toBeDefined();
  });

  it("calls onRowClick when a row is clicked", () => {
    const data: Row[] = [{ id: 1, name: "Alpha" }];
    const onRowClick = vi.fn();
    render(<DataTable columns={columns} data={data} onRowClick={onRowClick} />);
    fireEvent.click(screen.getByText("Alpha"));
    expect(onRowClick).toHaveBeenCalledWith({ id: 1, name: "Alpha" });
  });

  it("shows empty state when data is empty", () => {
    render(<DataTable columns={columns} data={[]} empty="Nada aquí" />);
    expect(screen.getByText("Nada aquí")).toBeDefined();
  });

  it("sets data-accent='teg' on tr when rowAccent returns 'teg'", () => {
    const data: Row[] = [{ id: 1, name: "Alpha" }];
    render(
      <DataTable
        columns={columns}
        data={data}
        rowAccent={() => "teg"}
      />
    );
    const row = document.querySelector("tr[data-accent='teg']");
    expect(row).not.toBeNull();
  });
});

describe("StatTile", () => {
  it("renders label and value", () => {
    render(<StatTile label="PTEG activos" value={42} />);
    expect(screen.getByText("PTEG activos")).toBeDefined();
    expect(screen.getByText("42")).toBeDefined();
  });

  it("renders left rule span with aria-hidden when accent='teg'", () => {
    render(<StatTile label="TEG" value={5} accent="teg" />);
    const rule = document.querySelector("span[aria-hidden='true']");
    expect(rule).not.toBeNull();
  });
});

describe("Kbd", () => {
  it("renders children inside a kbd element", () => {
    render(<Kbd>P</Kbd>);
    const kbd = document.querySelector("kbd");
    expect(kbd).not.toBeNull();
    expect(kbd?.textContent).toBe("P");
  });
});
