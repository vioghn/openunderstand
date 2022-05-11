/*FreeMind - A Program for creating and viewing Mindmaps
 *Copyright (C) 2000-2006 Joerg Mueller, Daniel Polansky, Christian Foltin, Dimitri Polivaev and others.
 *
 *See COPYING for Details
 *
 *This program is free software; you can redistribute it and/or
 *modify it under the terms of the GNU General Public License
 *as published by the Free Software Foundation; either version 2
 *of the License, or (at your option) any later version.
 *
 *This program is distributed in the hope that it will be useful,
 *but WITHOUT ANY WARRANTY; without even the implied warranty of
 *MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *GNU General Public License for more details.
 *
 *You should have received a copy of the GNU General Public License
 *along with this program; if not, write to the Free Software
 *Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 */
/*
 * Created on 29.01.2006
 * Created by Dimitri Polivaev
 */
package freemind.modes.mindmapmode.attributeactors;

import freemind.controller.actions.generated.instance.UnregistryAttributeValueElementaryAction;
import freemind.controller.actions.generated.instance.XmlAction;
import freemind.modes.mindmapmode.MindMapController;
import freemind.modes.mindmapmode.actions.xml.AbstractActorXml;
import freemind.modes.mindmapmode.actions.xml.ActionPair;

public class UnregistryAttributeValueActor extends AbstractActorXml {

	public UnregistryAttributeValueActor(MindMapController mindMapModeController) {
		super(mindMapModeController);
	}

	public XmlAction createAction(String name, String value) {
		UnregistryAttributeValueElementaryAction action = new UnregistryAttributeValueElementaryAction();
		action.setName(name);
		action.setValue(value);
		return action;
	}

	public ActionPair createActionPair(String name, String value) {
		ActionPair actionPair = new ActionPair(
				createAction(name, value),
				((MindMapModeAttributeController) getAttributeController()).registryAttributeValueActor
						.createAction(name, value));
		return actionPair;
	}

	public void act(XmlAction action) {
		if (action instanceof UnregistryAttributeValueElementaryAction) {
			UnregistryAttributeValueElementaryAction unrregistryAttributeValueAction = (UnregistryAttributeValueElementaryAction) action;
			act(unrregistryAttributeValueAction.getName(),
					unrregistryAttributeValueAction.getValue());
		}

	}

	private void act(String name, String value) {
		getAttributeRegistry().getElement(name).removeValue(value);
	}

	public Class getDoActionClass() {
		return UnregistryAttributeValueElementaryAction.class;
	}

}
