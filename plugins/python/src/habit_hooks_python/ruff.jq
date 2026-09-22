# What ruff's own JSON means as findings: each violation's code becomes the
# smell it names in the catalogue, grouped into one finding per smell (jq's
# group_by sorts them, as the old helper's `sorted` did). A code with no entry
# above is not dropped — it passes through as a finding under the code's own
# name, where the run's `uncoached` handling catches it: a code nobody
# catalogued is still a violation the project should see and tune, and a drop
# would be a clean run nobody ran.
def smell:
  . as $code
  | {"C901": "high-complexity",
   "PLR0913": "too-many-parameters",
   "PLR0915": "oversized-function",
   "F841": "unused-variable",
   "F401": "unused-import",
   "BLE001": "swallowed-exception",
   "invalid-syntax": "parse-error"}[$code] // $code;

group_by(.code | smell)
| map({smell: (.[0].code | smell),
       details: {},
       issues: map({key: .filename,
                    details: {file: .filename,
                              line: .location.row,
                              column: .location.column,
                              message: .message,
                              source: ("ruff:" + .code)}})})
