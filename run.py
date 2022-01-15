from canvas.canvas import Canvas

with Canvas() as bot:
    bot.get_first_page()
    bot.login()
    bot.get_course_links()
    bot.get_course_materials()
