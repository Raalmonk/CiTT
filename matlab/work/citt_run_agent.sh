#!/bin/zsh
stdout='/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_stdout.log'
stderr='/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_stderr.log'
status_file='/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_status.txt'
exit_file='/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_exit_status.txt'
attempt_file='/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_attempt.txt'
max_attempts=4
delay_seconds=20
: > "$stdout"
: > "$stderr"
rm -f "$exit_file" "$attempt_file"
echo running > "$status_file"
attempt=1
final_status=1
while [ "$attempt" -le "$max_attempts" ]; do
  echo "===== External agent attempt ${attempt}/${max_attempts} =====" >> "$stdout"
  cat '/Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_agent_task.md' | '/Applications/Codex.app/Contents/Resources/codex' exec --dangerously-bypass-approvals-and-sandbox --cd '/Users/Raalm/Documents/GitHub/CiTT/matlab' - >> "$stdout" 2>> "$stderr"
  final_status=$?
  echo "$attempt" > "$attempt_file"
  if [ "$final_status" -eq 0 ]; then
    break
  fi
  combined=$(cat "$stdout" "$stderr" 2>/dev/null | tr '[:upper:]' '[:lower:]')
  if printf '%s' "$combined" | grep -Eq 'daily quota|terminalquotaerror|generate_requests_per_model_per_day|you have exhausted your daily quota'; then
    break
  fi
  if [ "$attempt" -ge "$max_attempts" ]; then
    break
  fi
  if printf '%s' "$combined" | grep -Eq '503|service unavailable|temporarily unavailable|internal server error|server error|deadline exceeded|connection reset|econnreset|etimedout|socket hang up'; then
    echo "CiTT retrying external agent after transient service/API error in ${delay_seconds}s." >> "$stderr"
    sleep "$delay_seconds"
    attempt=$((attempt + 1))
    continue
  fi
  break
done
echo "$final_status" > "$exit_file"
if [ "$final_status" -eq 0 ]; then
  echo completed > "$status_file"
else
  echo failed > "$status_file"
fi
exit "$final_status"
