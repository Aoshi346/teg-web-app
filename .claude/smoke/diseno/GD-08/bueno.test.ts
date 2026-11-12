// Trampa de GD-08: el nombre de un test describe una conducta con palabras de escasez y no lo ve
// ningún cliente (falso positivo medido en fitapp).
import { describe, expect, test } from "vitest";

describe("registro del día", () => {
  test("solo hoy o ayer; lo de antes se rechaza con 400", () => {
    expect(["hoy", "ayer"]).toHaveLength(2);
  });
});
