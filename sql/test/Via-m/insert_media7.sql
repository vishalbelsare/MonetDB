select add_media((select event_id from event where event_name = 'event 1'), (select max(media_description_id) + 1 from media_description), 'description 3', 1, 25, 125);
