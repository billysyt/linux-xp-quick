-- SPDX-License-Identifier: MIT
local predictions = require('linux_xp_quick.predictions')
local keys = require('linux_xp_quick.keys')
local M = {}
local MARK = '~'
local PROPERTY = 'linux_xp_quick_head'
local ACCEPT, PASS = 1, 2

local function arm(ctx, state, text)
  local head = predictions.last_character(text)
  state.pending = predictions.has(head)
  ctx:set_property(PROPERTY, state.pending and head or '')
end

local function show(ctx, state)
  if state.pending and not state.busy and ctx.input == '' then
    state.pending, state.busy = false, true
    ctx:push_input(MARK)
    state.busy = false
  end
end

local function cancel(ctx, state)
  state.pending, state.busy = false, true
  ctx:set_property(PROPERTY, '')
  ctx:clear()
  state.busy = false
end

function M.init(env)
  local ctx = env.engine.context
  env.state = {pending=false, busy=false}
  env.page_size = env.engine.schema.config:get_int('menu/page_size') or 9
  env.connections = {
    ctx.commit_notifier:connect(function(c) arm(c, env.state, c:get_commit_text()) end),
    ctx.update_notifier:connect(function(c) show(c, env.state) end),
  }
end

function M.fini(env)
  for _, connection in ipairs(env.connections or {}) do connection:disconnect() end
end

function M.func(key, env)
  if key:release() then return PASS end
  local ctx, state = env.engine.context, env.state
  if ctx:get_option('ascii_mode') then return PASS end

  -- One radical uses Rime's normal Space commit; two radicals page the menu.
  if key.keycode == 0x20 and keys.plain(key) and ctx.input:match('^[a-z][a-z]$') then
    env.engine:process_key(KeyEvent('Page_Down'))
    return ACCEPT
  end
  -- A literal tilde is not a prediction unless a committed head is present.
  if ctx.input ~= MARK or ctx:get_property(PROPERTY) == '' then return PASS end
  if key.keycode == 0xffe1 or key.keycode == 0xffe2 then return PASS end

  local number = keys.prediction_number(key)
  if number then
    local segment = ctx.composition:back()
    local selected = segment and segment.selected_index or 0
    local page_start = math.floor(selected / env.page_size) * env.page_size
    local tail = predictions.tails(ctx:get_property(PROPERTY))[page_start + number]
    if tail then
      cancel(ctx, state)
      env.engine:commit_text(tail)
      arm(ctx, state, tail)
      show(ctx, state)
    end
    return ACCEPT
  end

  if keys.navigation(key.keycode) and keys.plain(key) then return PASS end
  local escape = key.keycode == 0xff1b
  cancel(ctx, state)
  return escape and ACCEPT or PASS
end

return M
