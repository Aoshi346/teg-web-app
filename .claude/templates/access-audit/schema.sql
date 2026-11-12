-- Registro de accesos: solo INSERT para la app y cadena de hash por segmento diario.
-- Patrón: .claude/patterns/stack/backend-access-audit.md (léelo antes de copiar esto).
--
-- Roles que se esperan (los crea quien administra la base, NO la migración de la app):
--   audit_owner   dueño de la tabla y de las funciones; no lo usa la app
--   app_user      el rol con el que se conecta Django: INSERT y SELECT, nada más
--   audit_purger  el único que puede borrar; el trigger no comprueba que borre segmentos enteros
--                 caducados (lo hace su tarea de purga): un borrado parcial solo lo caza el ancla
-- En Django va en una migración con RunSQL (patrón §3), ejecutada como audit_owner.

CREATE TABLE access_event (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- Lo pone el trigger con el reloj del servidor: lo que mande la app se ignora.
    ts          timestamptz NOT NULL DEFAULT clock_timestamp(),
    segment     date        NOT NULL,
    seq         bigint      NOT NULL,
    actor_id    text        NOT NULL CHECK (actor_id <> ''),
    actor_role  text        NOT NULL,
    subject_ref text        NOT NULL,          -- seudónimo HMAC, nunca el id en claro
    resource    text        NOT NULL,          -- modelo#pk o apartado
    fields      text        NOT NULL DEFAULT '', -- nombres de campo separados por coma, nunca valores
    action      text        NOT NULL CHECK (action IN ('read', 'create', 'update', 'delete', 'export')),
    result      text        NOT NULL CHECK (result IN ('allowed', 'denied')),
    reason      text        NOT NULL DEFAULT '',
    context     text        NOT NULL DEFAULT '', -- tenant, sesión hasheada, IP truncada
    prev_hash   char(64)    NOT NULL,
    hash        char(64)    NOT NULL,
    UNIQUE (segment, seq)
);

-- Forma canónica: cada parte como «longitud:valor», unidas por «|». Sin ambigüedad aunque un valor
-- lleve el separador. chain.py la reproduce carácter a carácter.
CREATE FUNCTION access_event_canon(VARIADIC parts text[]) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT string_agg(length(p)::text || ':' || p, '|' ORDER BY i)
    FROM unnest(parts) WITH ORDINALITY AS t(p, i)
$$;

CREATE FUNCTION access_event_chain() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
    last_seq  bigint;
    last_hash char(64);
BEGIN
    NEW.ts := clock_timestamp();
    NEW.segment := (NEW.ts AT TIME ZONE 'UTC')::date;
    -- Un candado por segmento: dos inserciones a la vez no pueden leer la misma cabeza.
    PERFORM pg_advisory_xact_lock(hashtext('access_event:' || NEW.segment::text));
    SELECT seq, hash INTO last_seq, last_hash
      FROM access_event WHERE segment = NEW.segment ORDER BY seq DESC LIMIT 1;
    NEW.seq := coalesce(last_seq, 0) + 1;
    NEW.prev_hash := coalesce(last_hash, repeat('0', 64));
    NEW.hash := encode(sha256(convert_to(NEW.prev_hash || access_event_canon(
        NEW.segment::text, NEW.seq::text,
        to_char(NEW.ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        NEW.actor_id, NEW.actor_role, NEW.subject_ref, NEW.resource, NEW.fields,
        NEW.action, NEW.result, NEW.reason, NEW.context), 'UTF8')), 'hex');
    RETURN NEW;
END $$;

CREATE TRIGGER access_event_chain BEFORE INSERT ON access_event
    FOR EACH ROW EXECUTE FUNCTION access_event_chain();

-- Segunda barrera, por si alguien concede UPDATE por error: nadie modifica una fila, y solo
-- audit_purger borra. Quien es dueño de la tabla puede desactivar esto: para él están la cadena
-- y el ancla externa (patrón §4).
CREATE FUNCTION access_event_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' AND current_user = 'audit_purger' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'access_event es de solo inserción (% bloqueado para %)', TG_OP, current_user;
END $$;

CREATE TRIGGER access_event_no_update BEFORE UPDATE OR DELETE ON access_event
    FOR EACH ROW EXECUTE FUNCTION access_event_immutable();
CREATE TRIGGER access_event_no_truncate BEFORE TRUNCATE ON access_event
    FOR EACH STATEMENT EXECUTE FUNCTION access_event_immutable();

REVOKE ALL ON access_event FROM PUBLIC;
-- SELECT porque el INSERT de Django lleva RETURNING id, y para la extracción por persona (art. 15).
GRANT INSERT, SELECT ON access_event TO app_user;
GRANT SELECT, DELETE ON access_event TO audit_purger;
