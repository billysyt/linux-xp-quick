-- SPDX-License-Identifier: MIT
local predictions = require('linux_xp_quick.predictions')
local keys = require('linux_xp_quick.keys')
local M = {}
local MARK = predictions.marker
local PROPERTY = predictions.property
local ACCEPT, PASS = 1, 2

local function after_commit(ctx, state)
  if state.next_radical then
    state.after_commit = state.next_radical
  elseif not state.replaying and not ctx:get_option('ascii_mode') then
    local head = predictions.last_character(ctx:get_commit_text())
    if predictions.has(head) then
      if ctx:get_property(PROPERTY) ~= head then ctx:set_property(PROPERTY, head) end
      state.after_commit = MARK
    end
  end
end

local function update(ctx, state)
  local input = state.after_commit
  state.after_commit, state.next_radical = nil, nil
  if input and ctx.input == '' then ctx:push_input(input) end
end

function M.init(env)
  local ctx = env.engine.context
  local state = {}
  env.state = state
  env.page_size = env.engine.schema.config:get_int('menu/page_size') or 9
  env.connections = {
    ctx.commit_notifier:connect(function(c) after_commit(c, state) end),
    ctx.update_notifier:connect(function(c) update(c, state) end),
    ctx.option_update_notifier:connect(function(c, name)
      if name == 'ascii_mode' and c:get_option(name) and c.input == MARK then c:clear() end
    end),
  }
end

function M.fini(env)
  for _, connection in ipairs(env.connections or {}) do connection:disconnect() end
end

function M.func(key, env)
  if key:release() then return PASS end
  local ctx, state = env.engine.context, env.state
  if ctx:get_option('ascii_mode') then return PASS end
  local code = key.keycode
  if code == 0xffe5 then return PASS end
  local plain = keys.plain(key)
  if key:caps() and not (key:ctrl() or key:alt() or key:super()) then
    -- XKB capitalizes letter keycodes, and Rime bindings match the lock modifier.
    local name = key:repr():gsub('Lock%+', '', 1)
    if plain and code >= 0x41 and code <= 0x5a then name = string.char(code + 0x20) end
    return env.engine:process_key(KeyEvent(name)) and ACCEPT or PASS
  end
  local radical = plain and code >= 0x61 and code <= 0x7a
  local input = ctx.input

  if input == MARK then
    if radical then
      -- Replace the prediction in one composition update.
      ctx.input = string.char(code)
      return ACCEPT
    end
    if code == 0xffe1 or code == 0xffe2 then return PASS end

    local number = keys.prediction_number(key)
    if number then
      local segment = ctx.composition:back()
      if segment then
        local page_start = math.floor(segment.selected_index / env.page_size) * env.page_size
        ctx:select(page_start + number - 1)
      end
      return ACCEPT
    end

    -- The application handles Left and Right after a character is committed.
    if plain and code ~= 0xff51 and code ~= 0xff53 and keys.navigation(code) then return PASS end
    ctx:clear()
    return code == 0xff1b and ACCEPT or PASS
  end

  if state.next_radical then
    if code == 0xff1b or (plain and code == 0xff08) then
      state.next_radical = nil
      return code == 0xff08 and ACCEPT or PASS
    end
    -- Let native selection finish the current code before starting the next.
    local selecting = code == 0xff0d or code == 0xff8d
      or (code >= 0x31 and code <= 0x39) or (code >= 0xffb1 and code <= 0xffb9)
    if plain and code < 0xffe1 and not keys.navigation(code) and not selecting then
      local next_radical = state.next_radical
      state.next_radical, state.replaying = nil, true
      env.engine:process_key(KeyEvent(next_radical))
      state.replaying = false
      return PASS
    end
  end

  local full_code = #input == 2 and input:match('^[a-z][a-z]$')
  if full_code and plain and code == 0x20 then
    env.engine:process_key(KeyEvent('Page_Down'))
    return ACCEPT
  end
  if full_code and radical and not state.replaying and ctx.caret_pos == #input and ctx:has_menu() then
    -- A fast typist can press the next radical before selecting this code.
    state.next_radical = string.char(code)
    return ACCEPT
  end
  return PASS
end

return M
