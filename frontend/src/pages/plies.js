        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "手次原件和实盘重放",
  "module": "棋钟与手次",
  "caption": "棋钟与手次",
  "detail": "记录棋钟时间差、重复落点及提子数量。在棋盘上重放后记入提子见证。",
  "path": "/plies",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "game",
      "label": "对局"
    },
    {
      "name": "number",
      "label": "手次"
    },
    {
      "name": "gap",
      "label": "棋钟差秒"
    },
    {
      "name": "capture_claim",
      "label": "记录提子数"
    },
    {
      "name": "replayed",
      "label": "重放提子数"
    },
    {
      "name": "repeat_move",
      "label": "重复落点"
    },
    {
      "name": "witness",
      "label": "已重放"
    },
    {
      "name": "adjudicated",
      "label": "勘误后确认"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "attach_ply",
      "label": "登记棋谱手次",
      "path": "/plies/attach-ply",
      "fields": [
        {
          "name": "code",
          "label": "手次号",
          "kind": "text",
          "initial": "MV-32"
        },
        {
          "name": "game",
          "label": "对局号",
          "kind": "text",
          "initial": "G-41"
        },
        {
          "name": "number",
          "label": "手次",
          "kind": "int",
          "initial": 32
        },
        {
          "name": "gap",
          "label": "棋钟差秒",
          "kind": "float",
          "initial": 12
        },
        {
          "name": "capture_claim",
          "label": "原件提子",
          "kind": "int",
          "initial": 4
        },
        {
          "name": "repeat_move",
          "label": "落点重复",
          "kind": "bool",
          "initial": true
        }
      ],
      "help": "手次以裁判席原件为准。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "verify_replay",
      "label": "记录实盘重放",
      "path": "/plies/verify-replay",
      "fields": [
        {
          "name": "ply",
          "label": "手次号",
          "kind": "text",
          "initial": "MV-32"
        },
        {
          "name": "actual",
          "label": "棋盘重放提子",
          "kind": "int",
          "initial": 2
        }
      ],
      "help": "复核员逐子重放并保存实数。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "plan_dispatch",
      "label": "按分数派单占桌",
      "path": "/dispatch_orders/plan",
      "fields": [],
      "help": "复盘只有三张桌：按模型「核对提子」分数补满空桌，每局最多一桌；已重放或已封账的手次不再派。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已排单"
    },
    {
      "name": "claim_order",
      "label": "领单",
      "path": "/dispatch_orders/claim",
      "fields": [
        {
          "name": "code",
          "label": "派单号（手次号）",
          "kind": "text",
          "initial": "MV-32"
        }
      ],
      "help": "与换单同时提交时先落库者生效；先领到就照原单做。",
      "roles": [
        "reviewer"
      ],
      "success": "已领单"
    },
    {
      "name": "swap_order",
      "label": "换单（高分顶未领）",
      "path": "/dispatch_orders/swap",
      "fields": [
        {
          "name": "code",
          "label": "要换下的派单号",
          "kind": "text",
          "initial": "MV-32"
        },
        {
          "name": "ply",
          "label": "顶上来的手次号",
          "kind": "text",
          "initial": "MV-33"
        }
      ],
      "help": "仅「核对提子」分更高、且未领的单可被顶掉；被换下的单须重新领。",
      "roles": [
        "reviewer"
      ],
      "success": "已换单"
    },
    {
      "name": "report_captures",
      "label": "报实盘提子数",
      "path": "/dispatch_orders/report",
      "fields": [
        {
          "name": "code",
          "label": "派单号（手次号）",
          "kind": "text",
          "initial": "MV-32"
        },
        {
          "name": "actual",
          "label": "实盘提子数",
          "kind": "int",
          "initial": 2
        }
      ],
      "help": "领单人报完实盘提子数才腾桌、才准封账。",
      "roles": [
        "reviewer"
      ],
      "success": "已报数"
    }
  ],
  "sections": [
    {
      "caption": "复盘派单桌（三张）",
      "path": "/dispatch_orders",
      "unwrap": "orders",
      "view": "table",
      "columns": [
        {
          "name": "table_no",
          "label": "桌号"
        },
        {
          "name": "code",
          "label": "派单号"
        },
        {
          "name": "game",
          "label": "对局"
        },
        {
          "name": "score",
          "label": "核对提子分",
          "map": row => typeof row.score === 'number' ? row.score.toFixed(4) : row.score
        },
        {
          "name": "status",
          "label": "状态",
          "map": row => ({queued:'待领', claimed:'已领', done:'已报数', withdrawn:'已撤回'}[row.status] || row.status)
        },
        {
          "name": "claimed_by",
          "label": "领单人"
        },
        {
          "name": "actual",
          "label": "实盘提子数"
        },
        {
          "name": "bumped_from",
          "label": "顶下原单"
        }
      ]
    }
  ]
};

        export const {title} = page;
        export const key = "plies";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
