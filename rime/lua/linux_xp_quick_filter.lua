-- SPDX-License-Identifier: MIT
-- Hide the punctuation translator's literal marker on later prediction pages.
return function(translation, env)
  local ctx = env.engine.context
  local predicting = ctx.input == '~' and ctx:get_property('linux_xp_quick_head') ~= ''
  for candidate in translation:iter() do
    if not predicting or candidate.type == 'prediction' then yield(candidate) end
  end
end
