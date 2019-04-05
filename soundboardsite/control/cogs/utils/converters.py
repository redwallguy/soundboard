import datetime
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO)

# converter for reminder commands TODO resume Heroku reminder process when $$ acquired
def to_date(dt):
    dt_split = dt.split("/")
    if len(dt_split) != 4:
        logging.info("to_date converter Err 1")
        raise commands.BadArgument()
    else:
        try:
            month = int(dt_split[0])
            day = int(dt_split[1])
            year = int(dt_split[2])
        except ValueError:
            logging.info("to_date converter Err 2")
            raise commands.BadArgument()
        else:
            time_given = dt_split[3]
            time_split = time_given.split(":")
            if len(time_split) != 2:
                logging.info("to_date converter Err 3")
                raise commands.BadArgument()
            else:
                try:
                    hour = int(time_split[0])
                    minute = int(time_split[1])
                except ValueError:
                    logging.info("to_date converter Err 4")
                    raise commands.BadArgument()
                else:
                    try:
                        date = datetime.datetime(year=year,month=month,day=day,hour=hour,minute=minute,
                                                 tzinfo=datetime.timezone.utc)
                    except ValueError:
                        logging.info("to_date converter Err 5")
                        raise commands.BadArgument()
                    else:
                        if datetime.datetime.now(datetime.timezone.utc) - date > datetime.timedelta(seconds=0) or date - datetime.datetime.now(datetime.timezone.utc) > datetime.timedelta(weeks=2):
                            logging.info("to_date converter Err 6")
                            raise commands.BadArgument()
                        else:
                            return date
