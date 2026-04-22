import * as React from "react"
import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi } from "vitest"

import { Button } from "@shared/ui/button"
import { Input } from "@shared/ui/input"
import { Field } from "@shared/ui/Field"
import { Surface } from "@shared/ui/Surface"
import { SegmentedControl } from "@shared/ui/SegmentedControl"

describe("Button", () => {
  it("renders without crashing", () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole("button", { name: /click me/i })).toBeDefined()
  })

  it("default size is 40px tall via h-10 class", () => {
    render(<Button>Default</Button>)
    const btn = screen.getByRole("button")
    expect(btn.className).toContain("h-10")
  })

  it("applies focus ring classes (no dark: prefix)", () => {
    render(<Button>Focus</Button>)
    const btn = screen.getByRole("button")
    expect(btn.className).toContain("focus-visible:ring-2")
    expect(btn.className).toContain("focus-visible:ring-primary/50")
    expect(btn.className).not.toContain("dark:")
  })

  it("sets disabled state correctly", () => {
    render(<Button disabled>Disabled</Button>)
    const btn = screen.getByRole("button")
    expect(btn).toHaveProperty("disabled", true)
  })
})

describe("Input", () => {
  it("renders without crashing", () => {
    render(<Input placeholder="Type here" />)
    expect(screen.getByPlaceholderText("Type here")).toBeDefined()
  })

  it("has h-10 class for 40px height", () => {
    render(<Input placeholder="test" />)
    const input = screen.getByPlaceholderText("test")
    expect(input.className).toContain("h-10")
  })

  it("applies aria-invalid destructive styling", () => {
    render(<Input aria-invalid="true" placeholder="invalid" />)
    const input = screen.getByPlaceholderText("invalid")
    expect(input.className).toContain("aria-invalid:border-destructive")
  })

  it("does not have dark: classes", () => {
    render(<Input placeholder="no dark" />)
    const input = screen.getByPlaceholderText("no dark")
    expect(input.className).not.toContain("dark:")
  })
})

describe("Field", () => {
  it("links label to control via htmlFor and id", () => {
    render(
      <Field label="Email">
        <Input placeholder="enter email" />
      </Field>
    )
    const label = screen.getByText("Email")
    const input = screen.getByPlaceholderText("enter email")
    const labelFor = label.getAttribute("for")
    const inputId = input.getAttribute("id")
    expect(labelFor).toBeTruthy()
    expect(inputId).toBeTruthy()
    expect(labelFor).toBe(inputId)
  })

  it("exposes error via aria-describedby", () => {
    render(
      <Field label="Name" error="Required field">
        <Input placeholder="name" />
      </Field>
    )
    const input = screen.getByPlaceholderText("name")
    const describedBy = input.getAttribute("aria-describedby")
    expect(describedBy).toBeTruthy()
    const errorEl = document.getElementById(describedBy!)
    expect(errorEl).toBeTruthy()
    expect(errorEl?.textContent).toContain("Required field")
  })

  it("marks control as aria-invalid when error is provided", () => {
    render(
      <Field label="Name" error="Required">
        <Input placeholder="name" />
      </Field>
    )
    const input = screen.getByPlaceholderText("name")
    expect(input.getAttribute("aria-invalid")).toBe("true")
  })

  it("renders red asterisk when required", () => {
    render(
      <Field label="Title" required>
        <Input placeholder="title" />
      </Field>
    )
    const asterisk = screen.getByText("*")
    expect(asterisk).toBeDefined()
  })
})

describe("Surface", () => {
  it("renders children", () => {
    render(<Surface>Content</Surface>)
    expect(screen.getByText("Content")).toBeDefined()
  })

  it("renders status accent bar data attribute when status is set", () => {
    render(<Surface status="success">Card</Surface>)
    const surface = screen.getByText("Card").closest("[data-slot='surface']")
    expect(surface?.getAttribute("data-status")).toBe("success")
  })

  it("renders pending status data attribute", () => {
    render(<Surface status="pending">Card</Surface>)
    const surface = screen.getByText("Card").closest("[data-slot='surface']")
    expect(surface?.getAttribute("data-status")).toBe("pending")
  })

  it("renders destructive status data attribute", () => {
    render(<Surface status="destructive">Card</Surface>)
    const surface = screen.getByText("Card").closest("[data-slot='surface']")
    expect(surface?.getAttribute("data-status")).toBe("destructive")
  })

  it("no data-status attribute when status is none", () => {
    render(<Surface>Card</Surface>)
    const surface = screen.getByText("Card").closest("[data-slot='surface']")
    expect(surface?.getAttribute("data-status")).toBeNull()
  })

  it("adds interactive hover classes when interactive prop is set", () => {
    render(<Surface interactive>Interactive</Surface>)
    const surface = screen.getByText("Interactive").closest("[data-slot='surface']")
    expect(surface?.className).toContain("hover:shadow-md")
    expect(surface?.className).toContain("hover:-translate-y-0.5")
  })

  it("does not add interactive classes when interactive is false", () => {
    render(<Surface>Static</Surface>)
    const surface = screen.getByText("Static").closest("[data-slot='surface']")
    expect(surface?.className).not.toContain("hover:shadow-md")
  })
})

describe("SegmentedControl", () => {
  const options = [
    { value: "a", label: "Option A" },
    { value: "b", label: "Option B" },
    { value: "c", label: "Option C" },
  ]

  it("renders with role=radiogroup", () => {
    render(
      <SegmentedControl value="a" onChange={vi.fn()} options={options} />
    )
    expect(screen.getByRole("radiogroup")).toBeDefined()
  })

  it("renders options with role=radio", () => {
    render(
      <SegmentedControl value="a" onChange={vi.fn()} options={options} />
    )
    const radios = screen.getAllByRole("radio")
    expect(radios).toHaveLength(3)
  })

  it("selected option has aria-checked=true", () => {
    render(
      <SegmentedControl value="b" onChange={vi.fn()} options={options} />
    )
    const optionB = screen.getByRole("radio", { name: "Option B" })
    expect(optionB.getAttribute("aria-checked")).toBe("true")
  })

  it("unselected options have aria-checked=false", () => {
    render(
      <SegmentedControl value="a" onChange={vi.fn()} options={options} />
    )
    const optionB = screen.getByRole("radio", { name: "Option B" })
    expect(optionB.getAttribute("aria-checked")).toBe("false")
  })

  it("arrow right key moves selection to next option", () => {
    const onChange = vi.fn()
    render(
      <SegmentedControl value="a" onChange={onChange} options={options} />
    )
    const group = screen.getByRole("radiogroup")
    fireEvent.keyDown(group, { key: "ArrowRight" })
    expect(onChange).toHaveBeenCalledWith("b")
  })

  it("arrow left key moves selection to previous option (wraps)", () => {
    const onChange = vi.fn()
    render(
      <SegmentedControl value="a" onChange={onChange} options={options} />
    )
    const group = screen.getByRole("radiogroup")
    fireEvent.keyDown(group, { key: "ArrowLeft" })
    expect(onChange).toHaveBeenCalledWith("c")
  })

  it("Home key jumps to first option", () => {
    const onChange = vi.fn()
    render(
      <SegmentedControl value="c" onChange={onChange} options={options} />
    )
    const group = screen.getByRole("radiogroup")
    fireEvent.keyDown(group, { key: "Home" })
    expect(onChange).toHaveBeenCalledWith("a")
  })

  it("End key jumps to last option", () => {
    const onChange = vi.fn()
    render(
      <SegmentedControl value="a" onChange={onChange} options={options} />
    )
    const group = screen.getByRole("radiogroup")
    fireEvent.keyDown(group, { key: "End" })
    expect(onChange).toHaveBeenCalledWith("c")
  })

  it("clicking an option calls onChange", () => {
    const onChange = vi.fn()
    render(
      <SegmentedControl value="a" onChange={onChange} options={options} />
    )
    fireEvent.click(screen.getByRole("radio", { name: "Option C" }))
    expect(onChange).toHaveBeenCalledWith("c")
  })
})
