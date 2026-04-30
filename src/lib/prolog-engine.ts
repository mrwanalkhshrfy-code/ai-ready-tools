// @ts-nocheck
import pl from "tau-prolog";

export interface PrologResult {
  type: "success" | "error" | "info";
  text: string;
}

export function createPrologSession() {
  const session = pl.create(1000);

  return {
    run(program: string, query: string): PrologResult[] {
      const results: PrologResult[] = [];

      // Parse the program
      const parseResult = session.consult(program);
      if (parseResult !== true) {
        results.push({
          type: "error",
          text: `Parse error: ${parseResult?.args?.[0] || String(parseResult)}`,
        });
        return results;
      }

      // Parse the query
      const queryResult = session.query(query);
      if (queryResult !== true) {
        results.push({
          type: "error",
          text: `Query error: ${queryResult?.args?.[0] || String(queryResult)}`,
        });
        return results;
      }

      // Get answers
      let found = false;
      let limit = 50;
      
      const getAnswers = () => {
        session.answer({
          success: (answer: any) => {
            found = true;
            const formatted = pl.format_answer(answer);
            results.push({ type: "success", text: formatted });
            limit--;
            if (limit > 0) {
              getAnswers();
            } else {
              results.push({ type: "info", text: "... (limited to 50 results)" });
            }
          },
          fail: () => {
            if (!found) {
              results.push({ type: "error", text: "false." });
            }
          },
          error: (err: any) => {
            results.push({
              type: "error",
              text: `Runtime error: ${err?.args?.[0] || String(err)}`,
            });
          },
          limit: () => {
            results.push({ type: "info", text: "Time limit exceeded." });
          },
        });
      };

      getAnswers();
      return results;
    },
  };
}
