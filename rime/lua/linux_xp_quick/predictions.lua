-- SPDX-License-Identifier: MIT
-- Pure phrase lookup; no engine state or typing history is persisted.
local data = require('linux_xp_quick.data')
local M = {}

function M.last_character(text)
  return text and text:match('[%z\1-\127\194-\244][\128-\191]*$') or ''
end

function M.has(head)
  return data[head] ~= nil and #data[head] > 0
end

function M.tails(head)
  local result = {}
  for _, phrase in ipairs(data[head] or {}) do
    local tail = phrase:sub(#head + 1)
    if tail ~= '' then result[#result + 1] = tail end
    if #result == 99 then break end
  end
  return result
end

return M
