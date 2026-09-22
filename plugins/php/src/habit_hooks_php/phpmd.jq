# What phpmd's own JSON means as findings: each violation's rule becomes the
# smell it names in the catalogue, grouped into one finding per smell (jq's
# group_by sorts them). A rule with no entry above is not dropped — it passes
# through as a finding under the rule's own name, where the run's `uncoached`
# handling catches it; with the fixed codesize,unusedcode rulesets that is
# dormant in practice, but a dropped rule is a clean run nobody ran.
def smell:
  . as $rule
  | {"ExcessiveParameterList": "too-many-parameters",
     "CyclomaticComplexity": "high-complexity",
     "ExcessiveMethodLength": "oversized-function",
     "UnusedLocalVariable": "unused-variable"}[$rule] // $rule;

[.files[]? | . as $file
  | .violations[]?
  | {smell: (.rule | smell), file: $file.file,
    line: .beginLine, message: .description, rule: .rule}]
| group_by(.smell)
| map({smell: .[0].smell,
       details: {},
       issues: map({key: .file,
                    details: {file: .file,
                              line: .line,
                              message: .message,
                              source: ("phpmd:" + .rule)}})})
