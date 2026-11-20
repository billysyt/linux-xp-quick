-- SPDX-License-Identifier: MIT
-- Pure phrase lookup; no engine state or typing history is persisted.
local data = require('linux_xp_quick.data')
local M = {}
-- Internal input marker outside the keyboard's spelling and punctuation keys.
M.marker = '\1'
M.property = '_linux_xp_quick_head'

function M.last_character(text)
  return text and text:match('[%z\1-\127\194-\244][\128-\191]*$') or ''
end

function M.has(head)
  return data[head] ~= nil and #data[head] > 0
end

function M.phrases(head)
  return data[head] or {}
end

return M
