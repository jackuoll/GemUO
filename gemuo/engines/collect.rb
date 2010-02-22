#
#  GemUO
#
#  (c) 2005-2010 Max Kellermann <max@duempel.org>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 of the License.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

require 'gemuo/timer'
require 'gemuo/engines/base'
require 'gemuo/engines/walk'

module GemUO::Engines
    class CollectItems < Base
        include GemUO::TimerEvent

        def initialize(client, item_id)
            super(client)
            @item_id = item_id
        end

        def on_ingame
            next_item
        end

        def tick
            next_item
        end

        def drop_target
            backpack = @client.world.backpack
            return unless backpack
            @client.world.each_item_in(backpack) do
                |item|
                return item if item.item_id == @item_id
            end
            return backpack
        end

        def on_delete_entity(entity)
            if @holding && @holding.serial == entity.serial
                target = drop_target
                unless target
                    puts "no backpack\n"
                    stop
                    @client.signal_fire(:on_engine_failed, self)
                    return
                end
                @client << GemUO::Packet::Drop.new(@holding.serial, 0, 0, 0, target.serial)
                @holding = nil
                restart(0.5)
                @client.timer << self
            end
        end

        def distance2(position)
            dx = @client.world.player.position.x - position.x
            dy = @client.world.player.position.y - position.y
            return dx*dx + dy*dy
        end

        def nearest_item
            items = []
            @client.world.each_item do
                |item|
                items << item if item.item_id == @item_id && item.position && item.parent == nil
            end
            return if items.empty?
            items.sort! do
                |a,b|
                distance2(a.position) <=> distance2(b.position)
            end
            items[0]
        end

        def on_lift_reject(reason)
            puts "lift reject #{reason}\n"
            on_delete_entity(@holding)
        end

        def next_item
            item = nearest_item
            unless item
                puts "no item found\n"
                stop
                @client.signal_fire(:on_engine_complete, self)
                return
            end

            if item.position.x == @client.world.player.position.x &&
                    item.position.y == @client.world.player.position.y
                # lift item
                backpack = @client.world.backpack
                puts "lifting #{item} to #{backpack}\n"
                amount = item.amount
                amount = 1 unless amount && amount > 0
                @holding = item
                @client << GemUO::Packet::Lift.new(item.serial, amount)
            else
                puts "walk\n"
                @walk = GemUO::Engines::SimpleWalk.new(@client, item.position)
                @walk.start
            end
        end

        def on_engine_complete(engine)
            if engine == @walk
                puts "walk ok\n"
                @walk = nil
                next_item
            end
        end

        def on_engine_failed(engine)
            if engine == @walk
                puts "walk failed\n"
                @walk = nil
                @client.signal_fire(:on_engine_failed, self)
                return
            end
        end
    end
end

