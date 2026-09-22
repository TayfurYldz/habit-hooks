# What RuboCop's own JSON means as findings: each offence's cop becomes the
# smell it names in the catalogue, grouped into one finding per smell (jq's
# group_by sorts them). A cop with no entry above is not dropped — it passes
# through as a finding under the cop's own name, where the run's `uncoached`
# handling catches it: a cop that fired is one the project's own `.rubocop.yml`
# switched on (#171), so it belongs to the project, and a drop would be a clean
# run nobody ran.
def smell:
  . as $cop
  | {"Metrics/ParameterLists": "too-many-parameters",
     "Metrics/MethodLength": "oversized-function",
     "Metrics/BlockLength": "oversized-block",
     "Metrics/CyclomaticComplexity": "high-complexity",
     "Metrics/PerceivedComplexity": "high-complexity",
     "Metrics/AbcSize": "high-complexity",
     "Metrics/BlockNesting": "deep-nesting",
     "Lint/UselessAssignment": "unused-variable",
     "Lint/SuppressedException": "swallowed-exception",
     "Lint/Syntax": "parse-error"}[$cop] // $cop;

[.files[]? | . as $file
  | .offenses[]?
  | {smell: (.cop_name | smell), file: $file.path,
    line: .location.line, column: .location.column,
    message: .message, cop: .cop_name}]
| group_by(.smell)
| map({smell: .[0].smell,
       details: {},
       issues: map({key: .file,
                    details: {file: .file,
                              line: .line,
                              column: .column,
                              message: .message,
                              source: ("rubocop:" + .cop)}})})
