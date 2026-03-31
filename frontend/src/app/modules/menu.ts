export type ModuleLink = {
  id: string;
  label: string;
  href: string;
};

export const modulesMenu: ModuleLink[] = [
  { id: "tesg", label: "Trabajo Especial de Grado", href: "/modules/selected?project=tesg" },
  { id: "anteproyecto", label: "Anteproyecto", href: "/modules/selected?project=anteproyecto" },
];
