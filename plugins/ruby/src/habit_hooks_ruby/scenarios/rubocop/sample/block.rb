# frozen_string_literal: true

# frozen_string_literal: true

REPORTS = {
  'billing' => 'billing.csv',
  'report' => 'report.csv',
  'usage' => 'usage.csv'
}.freeze

Dir.glob('*.rb').each do |path|
  lines = File.readlines(path)
  total = lines.count
  blank = lines.count { |line| line.strip.empty? }
  comment = lines.count { |line| line.strip.start_with?('#') }
  code = total - blank - comment
  puts "#{path}: #{total} lines, #{code} code, #{blank} blank, #{comment} comment"
  longest = lines.max_by(&:length)
  puts "longest line: #{longest.length}" if longest
  shortest = lines.reject { |line| line.strip.empty? }.min_by(&:length)
  puts "shortest line: #{shortest.length}" if shortest
  average = total.zero? ? 0 : (lines.sum(&:length) / total)
  puts "average line: #{average}"
  words = lines.sum { |line| line.split.length }
  puts "words: #{words}"
  chars = lines.sum(&:length)
  puts "characters: #{chars}"
  files = Dir.glob('*.rb').count
  puts "ruby files seen: #{files}"
  stamped = Time.now.strftime('%Y-%m-%d')
  puts "generated at: #{stamped}"
  puts 'done'
  REPORTS.each do |name, file|
    out = File.join('tmp', file)
    File.write(out, "#{name},#{total},#{code}\n")
    puts "wrote #{out}"
  end
end
