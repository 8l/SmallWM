#include "x-events.h"

/**
 * Runs a single iteration of the event loop, by capturing an X event and
 * acting upon it.
 *
 * @return true if more events can be processed, false otherwise.
 */
bool XEvents::step()
{
  // Grab the next event from X, and then dispatch upon its type
  m_xdata.next_event(m_event);

  if (m_event.type == m_xdata.randr_event_offset + RRNotify)
    handle_rrnotify();
      
  switch(m_event.type)
  {
  case KeyPress:
    handle_keypress();
    break;
  case ButtonPress:
    handle_buttonpress();
    break;
  case ButtonRelease:
	  handle_buttonrelease();
    break;
  case MotionNotify:
	  handle_motionnotify();
    break;
  case MapNotify:
	  handle_mapnotify();
    break;
   case UnmapNotify:
   	handle_unmapnotify();
    break;
   case Expose:
   	handle_expose();
    break;
   case DestroyNotify:
   	handle_destroynotify();
    break;
  }

  return !m_done;
}

/**
 * Rebuilds the display graph whenever XRandR notifies us.
 */
void XEvents::handle_rrnotify()
{
  std::vector<Box> screens;
  m_xdata.get_screen_boxes(screens);
  m_clients.update_screens(screens);
}

/**
 * Handles keyboard shortcuts.
 */
void XEvents::handle_keypress()
{
  KeySym key = m_xdata.get_keysym(m_event.xkey.keycode);
  bool is_using_secondary_action = (m_event.xkey.state & SECONDARY_MASK);

  Window client = None;
  
  switch(m_config.hotkey)
  {
  case HK_MOUSE:
    {
      client = m_event.xkey.subwindow;
      if (client == None)
        client = m_event.xkey.window;
    }
    break;
  case HK_FOCUS:
    client = m_clients.get_focused();
    break;
  default:
    return;
  }

  KeyBinding binding(key, is_using_secondary_action);
  KeyboardAction action = m_config.key_commands.binding_to_action[binding];
    
  switch(action)
  {
  case RUN:
    if (!fork())
    {
      /* 
       * Here's why 'exec' is used in two different ways. First, it is
       * important to have /bin/sh process the shell command since it
       * supports argument parsing, which eases our burden dramatically.
       * 
       * Now, consider the process sequence as depicted below (where 'xterm'
       * is the user's chosen shell).
       * 
       * fork()
       * [creates process] ==> execl(/bin/sh, -c, /bin/sh, exec xterm)
       * # Somewhere in the /bin/sh source...
       * [creates process] ==> execl(/usr/bin/xterm, /usr/bin/xterm)
       * 
       * If we used std::system instead, then the first process after fork()
       * would stick around to get the return code from the /bin/sh. If 'exec'
       * were not used in the /bin/sh command line, then /bin/sh would stick
       * around waiting for /usr/bin/xterm.
       * 
       * So, to avoid an extra smallwm process sticking around, _or_ an
       * unnecessary /bin/sh process sticking around, use 'exec' twice.
       */
      execl("/bin/sh", "/bin/sh", "-c", "exec /usr/bin/dmenu_run", NULL);
      exit(1);
    }
    return;
  case CYCLE_FOCUS:
    {
      Window next_focused = m_focus_cycle.get_next();
      if (next_focused != None)
        m_clients.focus(next_focused);
    }
    return;
  case CYCLE_FOCUS_BACK:
    {
      Window prev_focused = m_focus_cycle.get_prev();
      if (prev_focused != None)
      m_clients.focus(prev_focused);
    }
    return;
  case EXIT_WM:
    m_done = true;
    return;
  case NEXT_DESKTOP:
    m_clients.next_desktop();
    return;
  case PREV_DESKTOP:
    m_clients.prev_desktop();
    return;
    
  }

  bool is_client = m_clients.is_client(client);
  
  switch(is_client)
  {
  case true:
    {
      switch(action)
      {
      case CLIENT_NEXT_DESKTOP:
        m_clients.client_next_desktop(client);
        return;
      case CLIENT_PREV_DESKTOP:
        m_clients.client_prev_desktop(client);
        return;
      case TOGGLE_STICK:
        m_clients.toggle_stick(client);
        return;
      case ICONIFY:
        m_clients.iconify(client);
        return;
      case MAXIMIZE:
        m_clients.change_mode(client, CPS_MAX);
        return;
      case REQUEST_CLOSE:
        m_xdata.request_close(client);
        return;
      case FORCE_CLOSE:
        m_xdata.destroy_win(client);
        return;
      case K_SNAP_TOP:
        m_clients.change_mode(client, CPS_SPLIT_TOP);
        return;
      case K_SNAP_BOTTOM:
        m_clients.change_mode(client, CPS_SPLIT_BOTTOM);
        return;
      case K_SNAP_LEFT:
        m_clients.change_mode(client, CPS_SPLIT_LEFT);
        return;
      case K_SNAP_RIGHT:
        m_clients.change_mode(client, CPS_SPLIT_RIGHT);
        return;
      case SCREEN_TOP:
        m_clients.to_relative_screen(client, DIR_TOP);
        return;
      case SCREEN_BOTTOM:
        m_clients.to_relative_screen(client, DIR_BOTTOM);
        return;
      case SCREEN_LEFT:
        m_clients.to_relative_screen(client, DIR_LEFT);
        return;
      case SCREEN_RIGHT:
        m_clients.to_relative_screen(client, DIR_RIGHT);
        return;
      case LAYER_ABOVE:
        m_clients.up_layer(client);
        return;
      case LAYER_BELOW:
        m_clients.down_layer(client);
        return;
      case LAYER_TOP:
        m_clients.set_layer(client, MAX_LAYER);
        return;
      case LAYER_BOTTOM:
        m_clients.set_layer(client, MIN_LAYER);
        return;

#define LAYER_SET(l) case LAYER_##l: \
      m_clients.set_layer(client, l); \
      return;

      LAYER_SET(1);
      LAYER_SET(2);
      LAYER_SET(3);
      LAYER_SET(4);
      LAYER_SET(5);
      LAYER_SET(6);
      LAYER_SET(7);
      LAYER_SET(8);
      LAYER_SET(9);

#undef LAYER_SET        
      }
    }
    return;
  }
}

/**
 * Handles a button click, which can do one of five things:
 *  - Launching a terminal
 *  - Deiconifying an icon
 *  - Start moving a window
 *  - Start resizing a window
 *  - Focusing a window
 */
void XEvents::handle_buttonpress()
{
    // We have to test both the window and the subwindow, because different
    // events use different windows
    bool is_client = false;
    if ( (m_clients.is_client(m_event.xbutton.window)) || 
         (m_clients.is_client(m_event.xbutton.subwindow)) )
        is_client = true;

    Icon *icon = m_xmodel.find_icon_from_icon_window(m_event.xbutton.window);

    if (!(is_client|| icon) && m_event.xbutton.button == LAUNCH_BUTTON 
            && m_event.xbutton.state == ACTION_MASK)
    {
        if (!fork())
        {
            /*
             * Here's why 'exec' is used in two different ways. First, it is
             * important to have /bin/sh process the shell command since it
             * supports argument parsing, which eases our burden dramatically.
             *
             * Now, consider the process sequence as depicted below (where 'xterm'
             * is the user's chosen shell).
             *
             * fork()
             * [creates process] ==> execl(/bin/sh, -c, /bin/sh, exec xterm)
             * # Somewhere in the /bin/sh source...
             * [creates process] ==> execl(/usr/bin/xterm, /usr/bin/xterm)
             *
             * If we used std::system instead, then the first process after fork()
             * would stick around to get the return code from the /bin/sh. If 'exec'
             * were not used in the /bin/sh command line, then /bin/sh would stick
             * around waiting for /usr/bin/xterm.
             *
             * So, to avoid an extra smallwm process sticking around, _or_ an 
             * unnecessary /bin/sh process sticking around, use 'exec' twice.
             */
            std::string shell = std::string("exec ") + m_config.shell;
            execl("/bin/sh", "/bin/sh", "-c", shell.c_str(), NULL);
            exit(1);
        }
    }
    else if (icon)
    {
        // Any click on an icon, whether or not the action modifier is
        // enabled or not, should deiconify a client
        m_clients.deiconify(icon->client);
    }
    else if (is_client && m_event.xbutton.state == ACTION_MASK)
    {
        if (m_event.xbutton.button != MOVE_BUTTON &&
                m_event.xbutton.button != RESIZE_BUTTON)
            return;

        // A left-click, with the action modifier, start resizing
        if (m_event.xbutton.button == MOVE_BUTTON)
            m_clients.start_moving(m_event.xbutton.subwindow);

        // A right-click, with the action modifier, start resizing
        if (m_event.xbutton.button == RESIZE_BUTTON)
            m_clients.start_resizing(m_event.xbutton.subwindow);
    }
    else if (is_client) // Any other click on a client focuses that client
        m_clients.force_focus(m_event.xbutton.window);
}

/**
 * Handles the release of a mouse button. This event is only expected when
 * a placeholder is going to be released, so the only possible action is to
 * stop moving/resizing.
 */
void XEvents::handle_buttonrelease()
{
    Window expected_placeholder = m_xmodel.get_move_resize_placeholder();
    
    // If this is *not* the current placeholder, then bail
    if (expected_placeholder != m_event.xbutton.window)
        return;

    MoveResizeState state = m_xmodel.get_move_resize_state();
    Window client = m_xmodel.get_move_resize_client();

    // Figure out the attributes of the placeholder, so that way we can do
    // the movements/resizes
    XWindowAttributes attrs;
    m_xdata.get_attributes(expected_placeholder, attrs);

    switch (state)
    {
    case MR_MOVE:
        m_clients.stop_moving(client, Dimension2D(attrs.x, attrs.y));
        break;
    case MR_RESIZE:
        m_clients.stop_resizing(client, 
                                Dimension2D(attrs.width, attrs.height));
        break;
    }
}

/**
 * Handles windows which have just shown themselves.
 *
 * Note that this can happen for any number of reasons. This method handles
 * the following scenarios:
 *
 *  - A genuinely new client which we want to manage
 *  - A genuinely new client, which happens to be a dialog window
 *  - A window which we aren't interested in managing
 *  - A client which is remapping itself, possibly from another desktop
 */
void XEvents::handle_mapnotify()
{
    Window being_mapped = m_event.xmap.window;

    add_window(being_mapped);
}

/**
 * This fixes issues where a client that was unmapped but not destroyed
 * would keep the focus (and cause SmallWM's keybindings to break), corrupt
 * the focus cycle, and do other nasty things. In the end, this ensures
 * that the window is unfocused, removed from the focus list, etc.
 */
void XEvents::handle_unmapnotify()
{
    Window being_unmapped = m_event.xmap.window;
    m_clients.unmap_client(being_unmapped);
}

/**
 * Handles the motion of the pointer. The only time that this ever applies is
 * when the user has moved the placeholder window - at all other times, this
 * event is ignored.
 */
void XEvents::handle_motionnotify()
{
    // Get the placeholder's current geometry, since we need to modify the
    // placeholder relative to the way it is now
    Window placeholder = m_xmodel.get_move_resize_placeholder();
    if (placeholder == None)
        return;
    XWindowAttributes attr;
    m_xdata.get_attributes(placeholder, attr);

    // Avoid needless updates by getting the most recent version of this
    // event
    m_xdata.get_latest_event(m_event, MotionNotify);

    // Get the difference relative to the previous position
    Dimension ptr_x, ptr_y;
    m_xdata.get_pointer_location(ptr_x, ptr_y);

    Dimension2D relative_change = m_xmodel.update_pointer(ptr_x, ptr_y);

    switch (m_xmodel.get_move_resize_state())
    {
    case MR_MOVE:
        // Update the position of the placeholder
        m_xdata.move_window(placeholder, 
            attr.x + DIM2D_X(relative_change), 
            attr.y + DIM2D_Y(relative_change));
        break;
    case MR_RESIZE:
        // Update the location being careful to avoid making the placeholder
        // have a negative size
        if (attr.width + DIM2D_X(relative_change) <= 0)
            DIM2D_X(relative_change) = 0;
        if (attr.height + DIM2D_Y(relative_change) <= 0)
            DIM2D_Y(relative_change) = 0;

        m_xdata.resize_window(placeholder,
            attr.width + DIM2D_X(relative_change),
            attr.height + DIM2D_Y(relative_change));
        break;
    }
}

/**
 * This event is only ever called on icon windows, and causes the icon
 * window to be redrawn.
 */
void XEvents::handle_expose()
{
    Icon *the_icon = m_xmodel.find_icon_from_icon_window(
        m_event.xexpose.window);

    if (!the_icon)
        return;

    // Avoid drawing over the current contents of the icon
    the_icon->gc->clear();

    int text_x_offset;
    if (m_config.show_icons)
    {
        // Get the application's pixmap icon, and figure out where to place
        // the text (since the icon goes to the left)
        XWMHints hints;
        bool has_hints = m_xdata.get_wm_hints(the_icon->client, hints);

        if (has_hints && hints.flags & IconPixmapHint)
        {
            // Copy the pixmap into the left side of the icon, keeping
            // its size. The width of the pixmap is the same as the
            // X offset of the window name (no padding is done here).
            Dimension2D pixmap_size = the_icon->gc->copy_pixmap(
                hints.icon_pixmap, 0, 0);
            text_x_offset = DIM2D_WIDTH(pixmap_size);
        }
        else
            text_x_offset = 0;
    }
    else
        text_x_offset = 0;
        
    std::string preferred_icon_name;
    m_xdata.get_icon_name(the_icon->client, preferred_icon_name);

    // The one thing that is strange here is that the Y offset is the entire
    // icon's height. This is because Xlib draws the text, starting at the
    // Y offset, from *bottom* to *top*. I don't know why.
    the_icon->gc->draw_string(text_x_offset, m_config.icon_height,
        preferred_icon_name);
}

/**
 * Handles a window which has been destroyed, by unregistering it.
 *
 * Note that ClientModelEvents will do the work of unregistering the client
 * if it is an icon, moving, etc.
 */
void XEvents::handle_destroynotify()
{
    Window destroyed_window = m_event.xdestroywindow.window;
    m_clients.remove_client(destroyed_window);
}

/**
 * Adds a window - this is exposed specifically so that smallwm.cpp can
 * access this method when it imports existing windows.
 *
 * @param window The window to add.
 */
void XEvents::add_window(Window window)
{
    // First, test if this client is already known to us - if it is, then
    // move it onto the current desktop
    if (m_clients.is_client(window))
    {
        Desktop const *mapped_desktop = m_clients.find_desktop(window);

        // Icons must be uniconified
        if (mapped_desktop->is_icon_desktop())
            m_clients.deiconify(window);

        // Moving/resizing clients must stop being moved/resized
        if (mapped_desktop->is_moving_desktop() || mapped_desktop->is_resizing_desktop())
        {
            Window placeholder = m_xmodel.get_move_resize_placeholder();
            m_xmodel.exit_move_resize();

            XWindowAttributes placeholder_attr;
            m_xdata.get_attributes(placeholder, placeholder_attr);

            if (mapped_desktop->is_moving_desktop())
                m_clients.stop_moving(window, 
                    Dimension2D(placeholder_attr.x, placeholder_attr.y));
            else if (mapped_desktop->is_resizing_desktop())
                m_clients.stop_resizing(window, 
                    Dimension2D(placeholder_attr.width, placeholder_attr.height));
        }

        // Clients which are currently stuck on all desktops don't need to have 
        // anything done to them. Everybody else has to be moved onto the 
        // current desktop.
        if (!mapped_desktop->is_all_desktop())
            m_clients.client_reset_desktop(window);

        return;
    }

    // So, this isn't an existing client. We have to figure out now if this is
    // even a client *at all* - override_redirect indicates if this client does
    // (false) or does not (true) want to be managed
    XWindowAttributes win_attr;
    m_xdata.get_attributes(window, win_attr);

    if (win_attr.override_redirect)
        return;

    // This is a new, manageable client - register it with the client database.
    // This requires we know 3 things:
    //  - What the client wants, with regards to its initial state - either
    //    visible or iconified
    //  - The client's position (we know this one)
    //  - The client's size (we know this one too)
    //
    //  The information about the initial state is given by XWMHints
    XWMHints hints;
    bool has_hints = m_xdata.get_wm_hints(window, hints);

    InitialState init_state = IS_VISIBLE;
    if (has_hints && hints.flags & StateHint && 
                     hints.initial_state == IconicState)
        init_state = IS_HIDDEN;

    std::string win_class;
    m_xdata.get_class(window, win_class);
    bool should_focus = 
        std::find(m_config.no_autofocus.begin(), 
                m_config.no_autofocus.end(), 
                win_class) == 
        m_config.no_autofocus.end();

    m_clients.add_client(window, init_state,
            Dimension2D(win_attr.x, win_attr.y), 
            Dimension2D(win_attr.width, win_attr.height),
            should_focus);

    // If the client is a dialog, this will be represented in the transient 
    // hint (which is None if the client is not a dialog, or not-None if it is)
    if (m_xdata.get_transient_hint(window) != None)
        m_clients.set_layer(window, DIALOG_LAYER);

    // Finally, execute the actions tied to the window's class

    if (m_config.classactions.count(win_class) > 0 && init_state != IS_HIDDEN)
    {
        ClassActions &action = m_config.classactions[win_class];

        if (action.actions & ACT_STICK)
            m_clients.toggle_stick(window);

        if (action.actions & ACT_MAXIMIZE)
            m_clients.change_mode(window, CPS_MAX);

        if (action.actions & ACT_SETLAYER)
            m_clients.set_layer(window, action.layer);

        if (action.actions & ACT_SNAP)
        {
            ClientPosScale mode;
            switch (action.snap) 
            {
                case DIR_LEFT:
                    mode = CPS_SPLIT_LEFT;
                    break;
                case DIR_RIGHT:
                    mode = CPS_SPLIT_RIGHT;
                    break;
                case DIR_TOP:
                    mode = CPS_SPLIT_TOP;
                    break;
                case DIR_BOTTOM:
                    mode = CPS_SPLIT_BOTTOM;
            }
            m_clients.change_mode(window, mode);
        }

        if (action.actions & ACT_MOVE_X || action.actions & ACT_MOVE_Y)
        {
            // This is exempt from the typical use for screen sizes, which is
            // relative to the window (that is, the screen size is the size of
            // the screen *that the window occupies*). This is because we can't
            // know what screen the user intended the window to be on.
            Box screen = m_clients.get_screen(window);

            m_clients.change_mode(window, CPS_FLOATING);

            Dimension win_x_pos = win_attr.x;
            Dimension win_y_pos = win_attr.y;

            if (action.actions & ACT_MOVE_X)
                win_x_pos = screen.width * action.relative_x;

            if (action.actions & ACT_MOVE_Y)
                win_y_pos = screen.height * action.relative_y;

            if (win_attr.x != win_x_pos || win_attr.x != win_y_pos)
                m_clients.change_location(window, win_x_pos, win_y_pos);
        }
    }
}
