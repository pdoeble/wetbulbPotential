declare module 'sql.js' {
  export interface Statement {
    bind(values: Record<string, unknown>): boolean;
    step(): boolean;
    getAsObject(): Record<string, unknown>;
    free(): void;
  }

  export interface Database {
    prepare(sql: string): Statement;
    close(): void;
  }

  export interface SqlJsStatic {
    Database: {
      new (data?: Uint8Array): Database;
    };
  }

  export default function initSqlJs(config?: {
    locateFile?: (file: string) => string;
  }): Promise<SqlJsStatic>;
}

